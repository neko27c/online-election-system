from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import PersonalInfo, Voter, VoteStatus
from electionapp.models import Election, Candidate, Party, CandidateVoteResult, PartyVoteResult
from django.db import IntegrityError, transaction

# ログイン状況確認
def get_login_voter(request):
    voter_id = request.session.get("voter_id")
    if not voter_id:
        return None

    return Voter.objects.filter(id=voter_id).select_related("person").first()

# 投票可能選挙の判定
def is_votable(voter, election):
    # エリア判定
    voter_area = voter.person.area
    available_areas = voter_area.get_self_and_parents()

    if election.area not in available_areas:
        return False

    # ステータス判定
    if election.status != "実施中":
        return False

    # すでに投票済みか
    if VoteStatus.objects.filter(
        person=voter.person,
        election=election
    ).exists():
        return False

    return True

# ログイン処理
def voter_login(request):
    if request.method == "POST":
        id_type = request.POST.get("id_type")
        login_id = request.POST.get("login_id")
        password = request.POST.get("password")

        # マイナンバー比較
        if id_type == "my_number":
            voter = Voter.objects.filter(
                person__my_number=login_id,
                vote_code__isnull=True
            ).first()

        # 投票用コード比較
        elif id_type == "vote_code":
            voter = Voter.objects.filter(
                vote_code=login_id
            ).first()

        # 該当アカウントが見つからなかった
        else:
            voter = None


        # アカウント存在チェック
        if voter is None:
            return render(request, "voter/login.html", {
                "error": "アカウントが見つかりません。"
            })

        # パスワードチェック
        if not check_password(password, voter.password):
            return render(request, "voter/login.html", {
                "error": "パスワードが正しくありません。"
            })

        # ログイン成功
        request.session.flush()
        request.session["voter_id"] = voter.id
        request.session["person_id"] = voter.person_id

        return redirect("dashboard")

    return render(request, "voter/login.html")



# ログアウト処理
def voter_logout(request):
    request.session.flush()
    return redirect('login')


# 投票者マイページ（投票状況一覧）
def dashboard(request):
    voter = get_login_voter(request)
    if not voter:
        return redirect("login")
    votes = VoteStatus.objects.filter(person_id=voter.person_id).order_by("-id")

    return render(request, 'voter/dashboard.html', {
        'voter': voter,
        'votes': votes,
    })


#  投票済みの選挙を除外した選挙一覧ページ
def election_list(request):
    voter = get_login_voter(request)
    if not voter:
        return redirect("login")

    # 実施中選挙取得
    elections = (
        Election.objects
        .filter(status="実施中")
        .order_by("end_date")
    )

    # 判定メソッドで絞る
    votable_elections = []
    for election in elections:
        if is_votable(voter, election):
            votable_elections.append(election)

    return render(request, 'voter/election_list.html', {
        'elections': votable_elections
    })

# 投票ページ
def vote_page(request, election_id):
    error = None
    voter = get_login_voter(request)
    if not voter:
        return redirect("login")
    election = get_object_or_404(Election, id=election_id)

    # 投票可否判定
    if not is_votable(voter, election):
        messages.error(request, "この選挙には投票できません。")
        return redirect('election_list')

    candidates = Candidate.objects.filter(election=election)

    # 衆議院・参議院のみ政党あり
    need_party = election.type in ["衆議院", "参議院"]
    party = Party.objects.all() if need_party else None

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")
        party_id = request.POST.get("party") if need_party else None

        # 入力チェック
        if not candidate_id:
            error="候補者を選択してください。"
        elif need_party and not party_id:
            error="政党を選択してください。"
        else:
            # 確認画面 or 投票確定へ
            request.session["vote_data"] = {
                "candidate_id": candidate_id,
                "party_id": party_id,
            }
            return redirect("vote_confirm", election_id=election.id)

    return render(request, "voter/vote.html", {
        "election": election,
        "candidates": candidates,
        "party": party,
        "need_party": need_party,
        "error": error,
    })

# 投票確認ページ
def vote_confirm(request, election_id):
    voter = get_login_voter(request)
    if not voter:
        return redirect("login")
    election = get_object_or_404(Election, id=election_id)

    # 投票可否判定
    if not is_votable(voter, election):
        messages.error(request, "この選挙には投票できません。")
        return redirect('election_list')

    vote_data = request.session.get("vote_data")
    if not vote_data:
        messages.error(request, "投票情報が存在しません。")
        return redirect('vote_page', election_id=election.id)

    candidate = get_object_or_404(Candidate, id=vote_data["candidate_id"], election=election)

    # 衆議院・参議院のみ政党あり
    party = None
    if election.type in ["衆議院", "参議院"]:
        party = get_object_or_404(Party, id=vote_data["party_id"])

    if request.method == "POST":
        try:
            with transaction.atomic():
                VoteStatus.objects.create(
                    person=voter.person,
                    election=election,
                    status="済",
                )
                    
                # 投票結果（候補者）
                candidate_vote_result, created = CandidateVoteResult.objects.get_or_create(
                    election=election,
                    candidate=candidate,
                    defaults={'result': 0}
                )
                candidate_vote_result.result += 1
                candidate_vote_result.save()
                
                # 投票結果（政党）
                if election.type in ["衆議院", "参議院"]:
                    party_vote_result, created = PartyVoteResult.objects.get_or_create(
                        election=election,
                        party=party,
                        defaults={'result': 0}
                    )
                    party_vote_result.result += 1
                    party_vote_result.save()
        except IntegrityError:
            messages.error(request, "すでに投票済みです。")
            return redirect("election_list")


        # セッション掃除
        del request.session["vote_data"]

        return redirect("vote_complete")

    return render(request, "voter/vote_confirm.html", {
        "election": election,
        "candidate": candidate,
        "party": party,
    })



# 投票完了ページ
def vote_complete(request):
    voter = get_login_voter(request)
    if not voter:
        return redirect("login")
    return render(request, 'voter/vote_complete.html')
