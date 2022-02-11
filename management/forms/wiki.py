from django import forms

from accounts.forms import BootStrapForm
from management.models import Wiki


class WikiAddForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = Wiki
        exclude = ['project', 'depth']

    def __init__(self, project_id, wiki_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 重置组件内容
        total_data_list = [("", "请选择")]
        print(wiki_id)
        if not wiki_id:
            data_list = Wiki.objects.filter(project=project_id).values_list("id", "title")
        else:
            data_list = Wiki.objects.filter(project=project_id).exclude(id=wiki_id).values_list("id", "title")
        total_data_list.extend(data_list)
        self.fields['parent'].choices = total_data_list
