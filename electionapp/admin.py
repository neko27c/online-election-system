from django.contrib import admin
from .models import Area, Election, Party, Candidate, CandidateVoteResult, PartyVoteResult

# Register your models here.

# モデルを管理サイトに登録
admin.site.register(Area)
admin.site.register(Election)
admin.site.register(Party)
admin.site.register(Candidate)
admin.site.register(CandidateVoteResult)
admin.site.register(PartyVoteResult)