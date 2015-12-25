// PurchaseListView
int_app.View = (function(View, Model, Collection){
  // 团购汇总视图，参数{group}
  View.GroupSummaryView = Backbone.View.extend({
    tagName: "div",
    className: 'detail-page',
    template: JST.group_summary,
    initialize: function(options) {
      this.group_id = options.group_id;

      this.products = new Collection.ProductList();
      this.purchases = new Collection.PurchaseList();
      this.wxUsers = new Collection.WxUserList();
      _.bindAll(this, "load", "fetchUserInfo");
      $.when(
        this.products.fetch({
          data: { group: this.group_id }
        }),
        this.purchases.fetch({
          data: { product__group: this.group_id }
        })
      ).then(this.fetchUserInfo).done(this.load);
    },
    fetchUserInfo: function(){
      var userList = this.purchases.pluck('buyer').join();
      return this.wxUsers.fetch({
        data: { id__in: userList }
      });
    },
    load: function() {
      // 构造需要输出到模板的信息
      total = 0;
      this.purchases.each(function(purchase){
        product = this.products.get(purchase.get('product'));
        total += product.get('price') * purchase.get('amount');
      }, this);

      var members = [];
      this.wxUsers.each(function(wxUser){
        amount = this.purchases.findWhere({buyer: wxUser.id}).get('amount');
        members.push({"headimgurl": wxUser.get('headimgurl'), "amount": amount});
      }, this);


      this.$el.html(this.template({
        "products": this.products.toJSON(),
        "total": total,
        "members": members
      }));
    },
    render: function() {
      $("body").append(this.el);
      return this;
    },
    close: function(){
      this.remove();
    }

  });
  return View;
})(int_app.View || {} , int_app.Model, int_app.Collection)
