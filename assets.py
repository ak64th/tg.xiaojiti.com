# coding=utf-8
from flask_assets import Bundle, Environment


# 设置js和css文件打包
assets = Environment()

bundles = {
    'layout': Bundle(
        'css/reset.css',
        'css/m.css',
        output='gen/layout.css',
        filters='cssmin'),
    'leader_js': Bundle(
        'js/models.js',
        'js/group_list_view.js',
        'js/product_list_view.js',
        'js/group_summary_view.js',
        output='gen/leader.js',
        filters='jsmin'),
    'member_js': Bundle(
        'js/models.js',
        'js/group_list_view.js',
        'js/purchase_list_view.js',
        'js/group_summary_view.js',
        output='gen/member.js',
        filters='jsmin',
    )
}

assets.register(bundles)