from django.db import models

# Create your models here.

# 管理者
class Administrator(models.Model):
    login_id=models.CharField()
    password=models.CharField()
    name=models.CharField(max_length=50)
    area=models.ForeignKey(
        'electionapp.Area',
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return self.name
    
