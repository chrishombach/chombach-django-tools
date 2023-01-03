from django.db import models

# Create your models here.
class List(models.Model):
    name = models.CharField(max_length = 200, unique=True)

class Item(models.Model):
    class ItemState(models.IntegerChoices):
        OPEN = 1
        IN_PROGRESS = 2
        DONE = 3
        DELETED = 0
    text = models.TextField(default='')
    list = models.ForeignKey(List, default='', on_delete=models.CASCADE)
    state = models.IntegerField(choices=ItemState.choices,
                               default=ItemState.OPEN)
    state_text = models.CharField(max_length=12,default='')
    def save(self, *args, **kwargs):
        try:
            self.state_text = dict(zip(self.ItemState.values, self.ItemState.labels))[self.state]
        except KeyError:
            raise KeyError( f'No state with State ID {self.state} defined!')
        super(Item, self).save(*args, **kwargs)
