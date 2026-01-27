from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from .models import Administrator
from django.views.generic import TemplateView, ListView, CreateView, FormView, View, DetailView, UpdateView
from electionapp.models import Election, Area, Candidate, Party, CandidateVoteResult, PartyVoteResult
from datetime import datetime, date
from .mixins import AdministratorLoginRequiredMixin
from django.contrib.auth import logout
from django.urls import reverse_lazy
from voter.models import Voter, PersonalInfo
from django.contrib import messages
import random, string
from django.core.serializers import serialize
import json
from django.utils import timezone
from django.core.exceptions import PermissionDenied

# Create your views here.

# 10桁の投票用コード自動生成
def generate_unique_voter_code(length=10):
    while True:
        # 英数字ランダム生成
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

        # データベースに存在しなければ採用
        if not Voter.objects.filter(vote_code=code).exists():
            return code

# ログイン
class AdministratorLoginView(View):
    template_name = 'administrator/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')

        error = "管理者IDまたはパスワードが間違っています。"

        try:
            admin = Administrator.objects.get(login_id=login_id)

            # パスワードチェック
            if check_password(password, admin.password):
                # セッションにログイン情報保存
                request.session.flush()
                request.session['login_id'] = admin.id
                request.session['name'] = admin.name
                # メインメニューに飛ばす
                return redirect('administrator:main_menu')

        except Administrator.DoesNotExist:
            pass

        return render(request, self.template_name, {'error': error})

# ログアウト
class AdministratorLogoutView(View):
    template_name = 'administrator/logout.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        logout(request)
        return redirect(reverse_lazy('administrator:login'))

# メインメニュー
class AdministratorMenuView(AdministratorLoginRequiredMixin, TemplateView):
    template_name='administrator/main_menu.html'

# 投票者アカウント作成
class VoterCreateView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/voter_create.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        person_id = request.POST.get("person_id")
        id_type = request.POST.get("id_type")
        password = request.POST.get("password")

        # 入力チェック
        if not person_id or not id_type or not password:
            return render(request, self.template_name,{
                "error": "すべての項目を入力してください。"
            })
            
        # valueErrorチェック
        if not person_id or not person_id.isdigit():
            return render(request, self.template_name, {
                "error": "person_id は数値で入力してください。"
            })

        # PersonalInfo 取得
        try:
            person = PersonalInfo.objects.get(id=person_id)
        except PersonalInfo.DoesNotExist:
            return render(request, self.template_name,{
                "error": "指定された person_id は存在しません。"
            })

        # マイナンバー認証アカウントは重複禁止
        if id_type == "my_number":
            if Voter.objects.filter(person=person, vote_code__isnull=True).exists():
                return render(request, self.template_name,{
                "error": "この個人情報にはすでにマイナンバー認証の投票者アカウントが存在します。"
            })

        # vote_code 発行（仮IDのみ）
        vote_code = None
        if id_type == "vote_code":
            vote_code = generate_unique_voter_code()

        # 作成
        Voter.objects.create(
            person=person,
            vote_code=vote_code,
            password=make_password(password),
        )

        messages.success(request, "登録が完了しました。")
        return redirect("administrator:voter_create")
    
# 投票者登録完了画面
class VoterCreateSuccessView(AdministratorLoginRequiredMixin, TemplateView):
    template_name='administrator/voter_create_success.html'
    
# 投票者の一覧表示
class VoterDeleteListView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/voter_delete.html"

    def get(self, request):
        keep = request.session.get("voter_delete_keep", False)
        if not keep and not request.GET:
            request.session.pop("voter_name", None)
            request.session.pop("birth_date", None)
            
        name = request.GET.get("name") or request.session.get("voter_name", "")
        birth_date_str = request.GET.get("birth_date") or request.session.get("birth_date", "")

        name = name.strip()
        
        if request.GET:
            request.session["voter_name"] = name
            request.session["birth_date"] = birth_date_str
        
        request.session.pop("voter_delete_keep", None)

        voters = Voter.objects.none()
        birth_date = None

        if birth_date_str:
            try:
                birth_date = date.fromisoformat(birth_date_str)
            except ValueError:
                birth_date = None

        if name and birth_date:
            voters = Voter.objects.filter(
                person__name=name,
                person__birth_date=birth_date
            ).order_by("-id")

        voter_list = [{
            "id": v.id,
            "name": v.person.name,
            "birth_date": v.person.birth_date,
            "address": v.person.address,
            "status": "仮" if v.vote_code else "マイナ",
        } for v in voters]

        return render(request, self.template_name, {
            "voters": voter_list,
            "name": name,
            "birth_date": birth_date_str,
        })

    def post(self, request):
        ids = request.POST.getlist("selected_voters")
        if ids:
            Voter.objects.filter(id__in=ids).delete()

        # 検索条件は保持
        request.session["voter_delete_keep"] = True
        return redirect("administrator:voter_delete_list")


# 投票者アカウント個別削除
class VoterDeleteView(AdministratorLoginRequiredMixin, View):
    def post(self, request, pk):
        voter = get_object_or_404(Voter, pk=pk)
        voter.delete()

        request.session["voter_delete_keep"] = True
        return redirect(reverse_lazy("administrator:voter_delete_list"))

# 選挙情報入力
class ElectionCreateView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/election_create.html"
    
    # データベースに登録されているエリア情報をjson形式で返す
    def get_area_data(self):
        def build_tree(area):
            return {
                "id": area.id,
                "name": area.name,
                "children": [
                    build_tree(child)
                    for child in Area.objects.filter(parent=area)
                ]
            }

        regions = [
            build_tree(area)
            for area in Area.objects.filter(parent__isnull=True)
        ]

        return json.dumps(regions, ensure_ascii=False)



    def get(self, request):
        regions_json = self.get_area_data()

        return render(request, self.template_name, {
            "regions_json": regions_json,
        })



    def post(self, request):
        # 入力データ取得
        name = request.POST.get("name")
        type = request.POST.get("type")
        area = request.POST.get("area")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        errors = {}
        start_date_obj = ""
        end_date_obj = ""

        # バリデーション
        if not name:
            errors["name"] = "選挙名を入力してください。"

        if not type:
            errors["type"] = "選挙区分を選択してください。"

        if not area:
            errors["area"] = "エリアを選択してください。"

        if not start_date:
            errors["start_date"] = "開始日を入力してください。"

        if not end_date:
            errors["end_date"] = "終了日を入力してください。"
            
        
        start_date_obj = None
        end_date_obj = None
        now = timezone.now()

        # 日付入力値チェック
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
            start_date_obj = timezone.make_aware(start_date_obj)

            if start_date_obj < now:
                errors["start_date"] = "開始日時は現在以降の日時を指定してください。"

        except (ValueError, TypeError, OverflowError):
            errors["start_date"] = "開始日時の入力形式が正しくありません。"

        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
            end_date_obj = timezone.make_aware(end_date_obj)

            if end_date_obj < now:
                errors["end_date"] = "終了日時は現在以降の日時を指定してください。"

        except (ValueError, TypeError, OverflowError):
            errors["end_date"] = "終了日時の入力形式が正しくありません。"

        # 日付前後チェック
        if not errors:
            if start_date_obj >= end_date_obj:
                errors["date_order"] = "終了日時は開始日時より後にしてください。"


        # 何かエラーがあればフォームに戻す
        if errors:
            # エリア情報取得
            regions_json = self.get_area_data()
            # 入力値も画面に返す
            return render(request, "administrator/election_create.html", {
                "errors": errors,
                "values": {
                    "name": name,
                    "type": type,
                    "area": area,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "regions_json": regions_json,
            })

        # 問題なければ登録
        # areaオブジェクト化
        area = Area.objects.get(id=request.POST["area"])
        # 管理者ID取得
        admin_id = request.session.get("login_id")
        if not admin_id:
            return redirect("administrator:administrator_login")

        # 登録処理
        Election.objects.create(
            name=name,
            type=type,
            area=area,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status="未実施",
            administrator_id=admin_id,
        )

        return redirect("administrator:election_list")

       
# 選挙一覧表示
class ElectionListView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/election_list.html"

    def get(self, request):
        q = request.GET.get("q", "").strip()

        elections = Election.objects.all()

        if q:
            elections = elections.filter(name__icontains=q)

        elections = elections.order_by("-start_date")

        return render(request, self.template_name, {
            "elections": elections,
            "q": q,  # 検索語をテンプレートに返す
        })

    # 操作ボタンの処理
    def post(self, request):
        election_id = request.POST.get("election_id")
        action = request.POST.get("action")  # "start" or "stop"

        election = get_object_or_404(Election, id=election_id)

        # status処理
        if action == "start" and election.status == "未実施":
            election.status = "実施中"

        elif action == "stop" and election.status == "実施中":
            election.status = "終了"

        election.save()

        return redirect("administrator:election_list")

# 選挙詳細
class ElectionDetailView(AdministratorLoginRequiredMixin, DetailView):
    model = Election
    template_name = 'administrator/election_detail.html'
    context_object_name = 'election'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        election = self.object

        # 立候補者一覧を取得
        candidates = Candidate.objects.filter(election=election)

        # 各候補者の投票数をVoteResultから取得
        candidate_data = []
        for candidate in candidates:
            vote_result = CandidateVoteResult.objects.filter(
                election=election,
                candidate=candidate
            ).first()
            vote_count = vote_result.result if vote_result else 0
            candidate_data.append({
                'candidate': candidate,
                'vote_count': vote_count
            })

        context['candidate_data'] = candidate_data
        return context
    
# 選挙編集
class ElectionUpdateView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/election_edit.html"

    # 未実施の選挙のみ編集可能
    def get_election(self, pk):
        election = get_object_or_404(Election, pk=pk)
        if election.status != "未実施":
            raise PermissionDenied("この選挙は編集できません")
        return election

    def get(self, request, pk):
        election = self.get_election(pk)
        candidates = Candidate.objects.filter(election=election)
        parties = Party.objects.all()

        return render(request, self.template_name, {
            "election": election,
            "candidates": candidates,
            "parties": parties,
        })

    def post(self, request, pk):
        election = self.get_election(pk)

        # 立候補者削除処理
        delete_id = request.POST.get("delete_candidate_id")
        if delete_id:
            candidate = get_object_or_404(
                Candidate,
                id=delete_id,
                election=election
            )
            candidate.delete()
            messages.success(request, "立候補者を削除しました。")
            return redirect("administrator:election_edit", pk=pk)

        # 立候補者追加処理
        name = request.POST.get("candidate_name")
        if not name:
            messages.error(request, "候補者名を入力してください。")
            return redirect("administrator:election_edit", pk=pk)

        party = None
        party_id = request.POST.get("party_id")
        if party_id:
            party = get_object_or_404(Party, id=party_id)

        Candidate.objects.create(
            election=election,
            name=name,
            party=party,
        )

        messages.success(request, "立候補者を登録しました。")
        return redirect("administrator:election_edit", pk=pk)

# 選挙結果
class ElectionResultView(AdministratorLoginRequiredMixin, View):
    template_name = "administrator/election_result.html"

    def get(self, request, election_id):
        election = get_object_or_404(Election, pk=election_id)

        # 候補者別投票結果
        candidate_results = (
            CandidateVoteResult.objects
            .filter(election=election)
            .select_related("candidate", "candidate__party")
            .order_by("-result")
        )

        # 政党別投票結果
        party_results = (
            PartyVoteResult.objects
            .filter(election=election)
            .select_related("party")
            .order_by("-result")
        )

        return render(request, self.template_name, {
            "election": election,
            "candidate_results": candidate_results,
            "party_results": party_results,
        })


# 立候補者情報の編集

