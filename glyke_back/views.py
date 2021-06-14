from django.http import HttpResponse
from django.shortcuts import render
import json
from django import forms
from django.utils.translation import gettext_lazy as _

from .forms import AddProductForm, SelectCategoryProductForm
from .models import Category, Product



def add_product_dynamic(request):
    context = {}
    category_fields = {}

    if not Category.objects.filter(is_active=True): return HttpResponse(_('No active categories'))

    if request.method == 'POST':
        if 'category' in request.POST:
            category_id = request.POST['category']
            category = Category.objects.get(id=category_id)

            for filter in category.filters.all():
                category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={
                'class': 'form-control', 
                }))

            CategoryFiltersForm = type('CategoryFiltersForm',
                                       (forms.Form,),
                                       category_fields)
            context['filter_form'] = CategoryFiltersForm()

            # try:
            #     category_filters = json.loads(category.filters)
            # except json.JSONDecodeError:
            #     category_filters = {}
        else:
            print("else2")
    else:
        print("else1")

    context['category_form'] = SelectCategoryProductForm(request.POST or None)
    context['product_form'] = AddProductForm()
    return render(request, "add_product.html", context)



    if request.method == 'POST':
        if 'recipe_name' in request.POST:
            ckb.recipe_name = int(request.POST['recipe_name'])
            ckb.save()
            try:
                content = json.loads(ckb.ingridients)
            except json.JSONDecodeError:
                content = {}
        else:
            for key in request.POST.keys():
                if key != 'csrfmiddlewaretoken':
                    content[key] = request.POST[key]
            ckb.ingridients = json.dumps(content)
            ckb.save()

    if ckb.recipe_name == 0:
        new_fields = {
            'cheese': forms.IntegerField(),
            'ham'   : forms.IntegerField(),
            'onion' : forms.IntegerField(),
            'bread' : forms.IntegerField(),
            'ketchup': forms.IntegerField()}
    else:
        new_fields = {
            'milk'  : forms.IntegerField(),
            'butter': forms.IntegerField(),
            'honey' : forms.IntegerField(),
            'eggs'  : forms.IntegerField()}

    DynamicIngridientsForm = type('DynamicIngridientsForm',
            (IngridientsForm,),
            new_fields)

    context['ingridients_form'] = DynamicIngridientsForm(content)
    context['cookbook_form'] = CookBookForm(request.POST or None)
    return render(request, "demo/dynamic.html", context)