# Generated by Django 3.2.5 on 2022-06-09 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dolfinrest', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dolfinimage',
            name='title',
        ),
        migrations.AddField(
            model_name='dolfinimage',
            name='filepath',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='dolfinimage',
            name='ipaddress',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='dolfinimage',
            name='imagefile',
            field=models.ImageField(upload_to='%Y/%m/%d/'),
        ),
    ]
