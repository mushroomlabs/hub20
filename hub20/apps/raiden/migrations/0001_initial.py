# Generated by Django 3.0.6 on 2020-06-11 16:13

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import hub20.apps.blockchain.fields
import hub20.apps.ethereum_money.models
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ethereum_money', '0001_initial'),
        ('blockchain', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenNetwork',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', hub20.apps.blockchain.fields.EthereumAddressField()),
                ('token', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ethereum_money.EthereumToken')),
            ],
        ),
        migrations.CreateModel(
            name='TokenNetworkChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.PositiveIntegerField()),
                ('participant_addresses', django.contrib.postgres.fields.ArrayField(base_field=hub20.apps.blockchain.fields.EthereumAddressField(), size=2)),
                ('token_network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='raiden.TokenNetwork')),
            ],
        ),
        migrations.CreateModel(
            name='TokenNetworkChannelStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', model_utils.fields.StatusField(choices=[('open', 'open'), ('settling', 'settling'), ('settled', 'settled'), ('unusable', 'unusable'), ('closed', 'closed'), ('closing', 'closing')], default='open', max_length=100, no_check_for_status=True, verbose_name='status')),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', verbose_name='status changed')),
                ('channel', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='raiden.TokenNetworkChannel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Raiden',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True, unique=True)),
                ('url', models.URLField(help_text='Root URL of server (without api/v1)')),
                ('token_networks', models.ManyToManyField(blank=True, to='raiden.TokenNetwork')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', model_utils.fields.StatusField(choices=[('open', 'open'), ('settling', 'settling'), ('settled', 'settled'), ('unusable', 'unusable'), ('closed', 'closed'), ('closing', 'closing')], default='open', max_length=100, no_check_for_status=True, verbose_name='status')),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', verbose_name='status changed')),
                ('identifier', models.PositiveIntegerField()),
                ('partner_address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True)),
                ('balance', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('total_deposit', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('total_withdraw', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('raiden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='raiden.Raiden')),
                ('token_network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='raiden.TokenNetwork')),
            ],
            options={
                'unique_together': {('raiden', 'token_network', 'partner_address'), ('raiden', 'token_network', 'identifier')},
            },
        ),
        migrations.CreateModel(
            name='TokenNetworkChannelEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=32)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='raiden.TokenNetworkChannel')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blockchain.Transaction')),
            ],
            options={
                'unique_together': {('channel', 'transaction')},
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('timestamp', models.DateTimeField()),
                ('identifier', models.BigIntegerField()),
                ('sender_address', hub20.apps.blockchain.fields.EthereumAddressField()),
                ('receiver_address', hub20.apps.blockchain.fields.EthereumAddressField()),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='raiden.Channel')),
            ],
            options={
                'unique_together': {('channel', 'timestamp', 'sender_address', 'receiver_address')},
            },
        ),
    ]
