# Generated by Django 2.2.3 on 2019-08-01 03:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import simplifytour.core.fields
import simplifytour.packages.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('content', simplifytour.core.fields.RichTextField(verbose_name='Content')),
                ('zip_import', models.FileField(blank=True, help_text="Upload a zip file containing images, and they'll be imported into this article-gallery.", upload_to='packages', verbose_name='Zip import')),
                ('featured_image', simplifytour.core.fields.FileField(blank=True, help_text='Featured image is displayed', null=True, upload_to='featured_images')),
                ('is_featured', models.BooleanField(default=False, help_text='Featured atricles are displayed', verbose_name='Is Featured')),
            ],
            options={
                'verbose_name': 'Article page',
                'verbose_name_plural': 'Article pages',
                'permissions': (('can_view', 'Can View'), ('can_modify', 'Can Modify')),
            },
        ),
        migrations.CreateModel(
            name='Guide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(default=None, help_text='Language spoken by Guide', max_length=255)),
                ('rate', models.DecimalField(decimal_places=2, default=None, help_text='Daily Rate', max_digits=6, null=True)),
                ('remarks', models.TextField(default=None, help_text='Any notes', max_length=255)),
            ],
            options={
                'verbose_name': 'Guide',
                'verbose_name_plural': 'Guides',
            },
        ),
        migrations.CreateModel(
            name='ItineraryItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Itinary title', max_length=255)),
                ('description', models.TextField(help_text='Brief description', max_length=255)),
                ('price', models.DecimalField(decimal_places=2, default=None, help_text='Price, just in case this single Itenary is requested.', max_digits=10, null=True)),
                ('days', models.DecimalField(decimal_places=2, default=1, help_text='No of days required for this Itenary.', max_digits=5)),
                ('duration', models.DecimalField(decimal_places=2, default=0, help_text='Time duration taken by this itinary item. 0 for full day.', max_digits=5)),
                ('starting_time', models.TimeField(default=None, help_text='Information purpose only. When will it start from, time of day?', null=True)),
                ('end_time', models.TimeField(default=None, help_text='Information purpose only. When is it supposed to complete, time of day?', null=True)),
            ],
            options={
                'verbose_name': 'Itinary Item',
                'verbose_name_plural': 'Itinary Items',
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keywords_string', models.CharField(blank=True, editable=False, max_length=500)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('slug', models.CharField(blank=True, help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, verbose_name='URL')),
                ('_meta_title', models.CharField(blank=True, help_text='Optional title to be used in the HTML title tag. If left blank, the main title field will be used.', max_length=500, null=True, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('gen_description', models.BooleanField(default=True, help_text='If checked, the description will be automatically generated from content. Uncheck if you want to manually set a custom description.', verbose_name='Generate description')),
                ('status', models.IntegerField(choices=[(1, 'Draft'), (2, 'Published')], default=2, help_text='With Draft chosen, will only be shown for admin users on the site.', verbose_name='Status')),
                ('publish_date', models.DateTimeField(blank=True, db_index=True, help_text="With Published chosen, won't be shown until this time", null=True, verbose_name='Published from')),
                ('expiry_date', models.DateTimeField(blank=True, help_text="With Published chosen, won't be shown after this time", null=True, verbose_name='Expires on')),
                ('short_url', models.URLField(blank=True, null=True)),
                ('in_sitemap', models.BooleanField(default=True, verbose_name='Show in sitemap')),
                ('titles', models.CharField(editable=False, max_length=1000, null=True)),
                ('content_model', models.CharField(editable=False, max_length=50, null=True)),
                ('in_menus', simplifytour.packages.fields.MenusField(blank=True, choices=[(1, 'Top navigation bar'), (2, 'Left-hand tree'), (3, 'Footer')], default=(1, 2, 3), max_length=100, null=True, verbose_name='Show in menus')),
                ('login_required', models.BooleanField(default=False, help_text='If checked, only logged in users can view this Package', verbose_name='Login required')),
                ('content', simplifytour.core.fields.RichTextField(verbose_name='Content')),
                ('include', simplifytour.core.fields.RichTextField(verbose_name='Include')),
                ('exclude', simplifytour.core.fields.RichTextField(verbose_name='Exclude')),
                ('featured_image', simplifytour.core.fields.FileField(blank=True, help_text='Focal image for this package.', null=True, upload_to='featured_images')),
                ('is_featured', models.BooleanField(default=False, help_text='Show in Homepage?', verbose_name='Is Featured')),
                ('is_archived', models.BooleanField(default=False, help_text='Archive this package?', verbose_name='Is Archived')),
                ('porter_required', models.BooleanField(default=False, help_text='Is porter necessary for this package?', verbose_name='Porter required')),
                ('porter_days', models.IntegerField(default=0, help_text='If porter is necessary, for how many days?')),
                ('guide_required', models.BooleanField(default=False, help_text='Is Guide necessary for this package?', verbose_name='Guide required')),
                ('guide_days', models.IntegerField(default=0, help_text='If guide is necessary, for how many days?')),
                ('other_info', jsonfield.fields.JSONField(default=[], editable=False, help_text='Other information of package')),
            ],
            options={
                'verbose_name': 'Package',
                'verbose_name_plural': 'Packages',
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Place',
                'verbose_name_plural': 'Places',
            },
        ),
        migrations.CreateModel(
            name='Porter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratio', models.DecimalField(decimal_places=1, default=None, help_text='Traveller to Porter ratio. (eg: 2 means 1 Porter for 2 Travellers)', max_digits=3, null=True)),
                ('count', models.IntegerField(default=0, help_text='No. of porters available in our system. 0 refers to unlimited')),
                ('rate', models.DecimalField(decimal_places=2, default=None, help_text='Rate of the porter', max_digits=6, null=True)),
                ('remarks', models.TextField(default=None, help_text='Any notes', max_length=255)),
            ],
            options={
                'verbose_name': 'Porter',
                'verbose_name_plural': 'Porters',
            },
        ),
        migrations.CreateModel(
            name='AdventurousPackage',
            fields=[
                ('package_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='packages.Package')),
            ],
            options={
                'verbose_name': 'Adventurous Package',
                'verbose_name_plural': 'Adventurous Packages',
            },
            bases=('packages.package',),
        ),
        migrations.CreateModel(
            name='TrekPackage',
            fields=[
                ('package_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='packages.Package')),
            ],
            options={
                'verbose_name': 'Trekking Package',
                'verbose_name_plural': 'Trekking Packages',
            },
            bases=('packages.package',),
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('standard', models.IntegerField(choices=[(1, 'Budget'), (2, 'Standard'), (3, 'Luxury')], default=1, help_text='Standard room type available')),
                ('marked_price', models.DecimalField(decimal_places=2, default=None, help_text='Marked price for this package', max_digits=10, null=True)),
                ('discounted_price', models.DecimalField(decimal_places=2, default=None, help_text='Discount price for this package', max_digits=10, null=True)),
                ('price_notes', models.CharField(help_text='Notes e.g seasonal and other', max_length=255)),
                ('min_group_size', models.PositiveSmallIntegerField(default=1, help_text='Minimun number of people on this package')),
                ('reduced_by', models.DecimalField(decimal_places=1, default=None, help_text='Discount percentace of this package', max_digits=3, null=True)),
                ('booking_amount', models.DecimalField(decimal_places=2, default=None, help_text='Price given on booking', max_digits=10, null=True)),
                ('max_group_size', models.PositiveSmallIntegerField(default=None, help_text='Maximum number of people on this package')),
                ('starting_date', jsonfield.fields.JSONField(default=[], help_text='Starting date of package')),
                ('extra_content', simplifytour.core.fields.RichTextField(blank=True, default=None, help_text='Include and Exclude on price', null=True, verbose_name='Extra Content')),
                ('is_archived', models.BooleanField(default=False, help_text='Archive this Price?')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='packages.Package')),
            ],
            options={
                'verbose_name': 'Price',
                'verbose_name_plural': 'Prices',
                'ordering': ['package', '-discounted_price'],
            },
        ),
        migrations.CreateModel(
            name='PackageItinerary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_order', simplifytour.core.fields.OrderField(null=True, verbose_name='Order')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='packages.ItineraryItem')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='packages.Package')),
            ],
            options={
                'ordering': ('_order',),
                'unique_together': {('package', 'item')},
            },
        ),
        migrations.CreateModel(
            name='PackageAddons',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='packages.ItineraryItem')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='packages.Package')),
            ],
            options={
                'unique_together': {('package', 'item')},
            },
        ),
        migrations.AddField(
            model_name='package',
            name='addons',
            field=models.ManyToManyField(blank=True, related_name='addon_packages_set', through='packages.PackageAddons', to='packages.ItineraryItem'),
        ),
        migrations.AddField(
            model_name='package',
            name='guides',
            field=models.ManyToManyField(blank=True, help_text='Guide options for this Package', related_name='packages', to='packages.Guide'),
        ),
        migrations.AddField(
            model_name='package',
            name='itinerary',
            field=models.ManyToManyField(through='packages.PackageItinerary', to='packages.ItineraryItem'),
        ),
        migrations.AddField(
            model_name='package',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='packages.Package'),
        ),
        migrations.AddField(
            model_name='package',
            name='porters',
            field=models.ManyToManyField(blank=True, help_text='Porter options for this Package', related_name='packages', to='packages.Porter'),
        ),
        migrations.AddField(
            model_name='package',
            name='provided_by',
            field=models.ForeignKey(help_text='Provider of this Package', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='package',
            name='site',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='sites.Site'),
        ),
        migrations.AddField(
            model_name='itineraryitem',
            name='ending_place',
            field=models.ForeignKey(blank=True, default=None, help_text='Where will it end?', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ending_place', to='packages.Place'),
        ),
        migrations.AddField(
            model_name='itineraryitem',
            name='packages',
            field=models.ManyToManyField(through='packages.PackageItinerary', to='packages.Package'),
        ),
        migrations.AddField(
            model_name='itineraryitem',
            name='provided_by',
            field=models.ForeignKey(help_text='Agency, who provided this itenary.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='itineraryitem',
            name='starting_place',
            field=models.ForeignKey(blank=True, default=None, help_text='Where does it start from?', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stating_place', to='packages.Place'),
        ),
        migrations.CreateModel(
            name='ArticleGalleryImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_order', simplifytour.core.fields.OrderField(null=True, verbose_name='Order')),
                ('file', simplifytour.core.fields.FileField(max_length=200, upload_to='packages', verbose_name='File')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='Title')),
                ('description', models.CharField(blank=True, max_length=1000, verbose_name='Description')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='packages.Article')),
            ],
            options={
                'verbose_name': 'Image',
                'verbose_name_plural': 'Images',
                'ordering': ('_order',),
            },
        ),
    ]
