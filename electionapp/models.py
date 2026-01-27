from django.db import models

# Create your models here.

# 地区
class Area(models.Model):
    name=models.CharField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    def get_self_and_parents(self):
        """
        自分自身 + 親エリアをすべて取得
        """
        areas = [self]
        current = self.parent

        while current:
            areas.append(current)
            current = current.parent

        return areas

# 選挙
class Election(models.Model):
    name=models.CharField(max_length=50)
    type=models.CharField(max_length=20)
    start_date=models.DateTimeField()
    end_date=models.DateTimeField()
    status=models.CharField(max_length=10)  # 入力例： "未実施", "実施中", "終了"
    administrator=models.ForeignKey(
        'administrator.Administrator',
        on_delete=models.PROTECT,
    )
    area=models.ForeignKey(
        Area,
        null=True,
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return self.name

  
# 所属  
class Party(models.Model):
    name=models.CharField()
    
    def __str__(self):
        return self.name
    
# 立候補者
class Candidate(models.Model):
    name=models.CharField()
    election=models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
    )
    party=models.ForeignKey(
        Party,
        on_delete=models.SET_NULL,
        null=True,
    )
    
    def __str__(self):
        return self.name
    
# 立候補者投票結果
class CandidateVoteResult(models.Model):
    election = models.ForeignKey(Election, on_delete=models.PROTECT)
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT)
    result = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['election', 'candidate'],
                name='unique_candidate_vote'
            )
        ]

# 政党投票結果
class PartyVoteResult(models.Model):
    election = models.ForeignKey(Election, on_delete=models.PROTECT)
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    result = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['election', 'party'],
                name='unique_party_vote'
            )
        ]

        