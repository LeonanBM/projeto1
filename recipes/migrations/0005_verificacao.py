# Generated by Django 4.2.9 on 2024-01-25 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0004_cadastroemanalise_analise_concluida"),
    ]

    operations = [
        migrations.CreateModel(
            name="Verificacao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("horario", models.DateTimeField(auto_now_add=True)),
                (
                    "pessoa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="recipes.pessoa"
                    ),
                ),
            ],
        ),
    ]
