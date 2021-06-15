from django.http import HttpResponse
from django.shortcuts import render
import json
from django import forms
from django.utils.translation import gettext_lazy as _

from .forms import AddProductForm, SelectCategoryProductForm
from .models import Category, Product


# TODO Devide into several functions and add comment and docstr
def add_product_dynamic(request):
    if not Category.objects.filter(is_active=True): return HttpResponse(_('No active categories'))

    category_fields = {}
    context = {}

    if request.method == 'POST':
        if 'category' in request.POST:
            category_id = request.POST['category']
            category = Category.objects.get(id=category_id)

            for filter in category.filters.all():
                # TODO Add some king of validation here to select the right input field
                category_fields[str(filter)] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',},), label=_(str(filter).capitalize()))
            # try:
            #     category_filters = json.loads(category.filters)
            # except json.JSONDecodeError:
            #     category_filters = {}
        else:
            #TODO
            print("else2")
        CategoryFiltersForm = type('CategoryFiltersForm',
                                       (forms.Form,),
                                       category_fields)
        context['filter_form'] = CategoryFiltersForm()

        temp_content = {'test2': 'тест', 'test1': 'тест', 'test3': 'тест', 'test5': 'тест'}
        filters_form = CategoryFiltersForm(temp_content)
        product_form = AddProductForm(request.POST)

        # print(dir(filters_form))
        print(filters_form.is_valid())
        # filters_form.full_clean()
        print('category' in request.POST) # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        print(filters_form.data)
        print(filters_form.cleaned_data)



        # if all([filters_form.is_valid(), product_form.is_valid(),]):
        #     print('----------------------------------------------------VALID')
        #     print(filters_form.cleaned_data)
        #     print(product_form.cleaned_data)



        #     # new_product, created = Product.objects.get_or_create(name='placeholder',
        #     #                                                      description = '',
        #     #                                                      category='placeholder',
        #     #                                                      tags='placeholder',
        #     #                                                      stock='placeholder',
        #     #                                                      # photos='placeholder',
        #     #                                                      cost_price='placeholder',
        #     #                                                      selling_price='placeholder',
        #     #                                                      discount_percent='placeholder',
        #     #                                                      profit='placeholder',
        #     #                                                     )
        # else:
        #     #TODO
        #     print("not valid")



    else:
        #TODO
        print("else1")

    context['category_form'] = SelectCategoryProductForm(request.POST or None)
    context['product_form'] = AddProductForm()
    return render(request, "add_product.html", context)

