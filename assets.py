# coding=utf-8
from flask_assets import Bundle, Environment
from webassets.filter import register_filter
from webassets.filter.jst import JST
import simplejson as json


# UnderscoreTemplateFilter
class UST(JST):
    """
    继承jst filter，用``_.template``代替jst自带的template函数。window.JST是存放模板函数的命名空间。
    生成的js文件类似下面：

        (function(){
          window.JST = window.JST || {};
          window.JST['group'] = _.template("
            <img src=\"/static/img/menu-cai-icon.png\"><span><%- group.title %></span>
          ");
        })();

    通过JST.group()来输出模板。

    """
    name = 'ust'

    def process_templates(self, out, hunks, **kwargs):
        namespace = 'window.JST'

        out.write("(function(){\n")

        out.write("%s = %s || {};\n" % (namespace, namespace))

        for name, hunk in self.iter_templates_with_base(hunks):
            # Make it a valid Javascript string.
            contents = json.dumps(hunk.data())

            out.write("%s['%s'] = " % (namespace, self._get_jst_name(name)))

            out.write("%s(%s);\n" % ('_.template', contents))

        out.write("})();")

register_filter(UST)


# 设置js和css文件打包
assets = Environment()

templates = Bundle(
    'jst/group.jst',
    'jst/group_summary.jst',
    'jst/purchase.jst',
    'jst/product.jst',
    filters='ust',
    output='gen/templates.js'
)

bundles = {
    'layout': Bundle(
        'css/reset.css',
        'css/m.css',
        output='gen/layout.css',
        filters='cssmin'
    ),
    'leader_js': Bundle(
        templates,
        'js/models.js',
        'js/group_list_view.js',
        'js/product_list_view.js',
        'js/group_summary_view.js',
        output='gen/leader.js',
        filters='jsmin'
    ),
    'member_js': Bundle(
        templates,
        'js/models.js',
        'js/group_list_view.js',
        'js/purchase_list_view.js',
        'js/group_summary_view.js',
        output='gen/member.js',
        filters='jsmin'
    )
}

assets.register(bundles)