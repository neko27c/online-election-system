from django.db import models

# Create your models here.

# 投票者情報
class PersonalInfo(models.Model):
    name = models.CharField()
    my_number=models.CharField(max_length=12, unique=True)
    gender = models.CharField(max_length=1)
    birth_date = models.DateField()
    address = models.CharField(max_length=50)
    nationality = models.CharField(max_length=20)
    area=models.ForeignKey(
        'electionapp.Area',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

# 投票者ログイン情報
class Voter(models.Model):
    person=models.ForeignKey(
        PersonalInfo,
        on_delete=models.CASCADE,
    )
    vote_code=models.CharField(null=True,blank=True,unique=True)
    password=models.CharField()
    
# 投票状況
class VoteStatus(models.Model):
    person=models.ForeignKey(
        PersonalInfo,
        on_delete=models.PROTECT,
    )
    election=models.ForeignKey(
        'electionapp.Election',
        on_delete=models.PROTECT,
    )
    status=models.CharField(max_length=1)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "election"],
                name="one_vote_status_per_person_per_election"
            )
        ]
