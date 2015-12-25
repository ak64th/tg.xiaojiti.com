// PurchaseListView
int_app.View = (function(View, Model, Collection){
  // 购买视图，参数{model, product}
  View.PurchaseView = Backbone.View.extend({
    tagName: 'div',
    className: "goods-item clear",
    events: {
      "click .plus":        "increaseAmount",
      "click .subtraction": "decreaseAmount",
      "click .toggle":      "toggle"
    },
    initialize: function (options) {
      this.product = options.product
      if (this.product instanceof Backbone.Model){
        this.product = this.product.toJSON();
      }
      this.listenTo(this.model, 'change', this.render);
    },
    template: JST.purchase,
    render: function(){
      this.$el.html(this.template({
        purchase: this.model.toJSON(),
        product: this.product
      }));
      return this;
    },
    increaseAmount: function(){
      currentAmount = this.model.get('amount');
      this.model.set('amount', currentAmount + 1);
    },
    decreaseAmount: function(){
      currentAmount = this.model.get('amount');
      this.model.set('amount', currentAmount - 1);
    },
    toggle: function(ev){
      this.model.set("checked", !this.model.get("checked"));
    }
  });

  // 购买列表视图，参数{wx_user_id,group_id}
  View.PurchaseListView = Backbone.View.extend({
    tagName: "div",
    id: "purchase_list_container",
    className: "goods-list",
    events: {
      "click .all-toggle": "toggleAll",
      "click .submit": "submitPurchase",
      "click .summary": "groupSummary",
    },
    initialize: function(options) {
      this.initUI();
      this.wx_user_id = options.wx_user_id
      this.group_id = options.group_id;
      this.subViews = [];
      this.products = new Collection.ProductList();
      this.purchases = new Collection.PurchaseList();
      this.listenTo(this.products, 'add', this.addOne);
      this.listenTo(this.purchases, 'change', this.countTotalPrice);
      this.listenTo(this.purchases, 'change:checked', this.checkToggleAll);
      this.products.fetch({
        data: { group: this.group_id }
      });
    },
    initUI: function(){
      this.$el.html('');
      purchase_panel_template = $('#purchase_panel_template').html();
      this.$el.append(purchase_panel_template);
    },
    addOne: function(product){
      purchase = new Model.PurchaseModel({
        "product": product.id,
        "buyer": this.wx_user_id,
        "amount": 1,
        "group": this.group_id,
        "checked": false
      });
      purchase.fetch({
        data:{
          product: product.id,
          group: this.group_id,
          buyer: this.wx_user_id
        },
        success: function(model){
          // 假若数据库里已经存在购买记录，checked设置为true
          model.set("checked", !model.isNew());
        }
      });
      this.purchases.add(purchase);
      view = new View.PurchaseView({model: purchase, product: product});
      this.subViews.push(view);
      this.$el.append(view.render().el);
    },
    countTotalPrice: function(){
      var totalPrice = 0;
      // 只选择那些已经勾选的购买
      purchases = this.purchases.filter(function(purchase){
        return purchase.get("checked");
      });
      _.each(purchases, function(purchase){
        product = this.products.get(purchase.get('product'));
        totalPrice += product.get('price') * purchase.get('amount');
      }, this);
      $('.goods-footer-bar .count').html('合计：'+ totalPrice +'<span>总额：'+ totalPrice +'</span>');
    },
    toggleAll: function(ev){
      $target = $(ev.currentTarget);
      $target.toggleClass('checked');
      checked = $target.hasClass('checked');
      this.purchases.each(function(purchase){
        purchase.set({"checked": checked});
      });
    },
    checkToggleAll: function(){
      if(this.purchases.every(function(purchase){
        return purchase.get('checked');
      })){
        $('.all-toggle').addClass('checked');
      } else {
        $('.all-toggle').removeClass('checked');
      }
    },
    syncAll: function(){
      // 遍历purchases集合，保存那些勾选了的购买记录，删除那些被取消了的记录
      this.purchases.each(function(purchase){
        if (purchase.get("checked")){
          if (purchase.hasChangedSinceLastSync()){
            purchase.save();
          }
        } else {
          // 因为是再each循环内，不能直接删除元素，只能clone元素后destroy发送delete请求
          purchase.clone().destroy();
        }
      });
    },
    submitPurchase: function() {
      this.syncAll();
      window.location.hash = '';
    },
    groupSummary: function(){
      this.syncAll();
      window.location.hash = '/group/' + this.group_id + '/summary/';
    },
    render: function() {
      $("body").append(this.el);
      return this;
    },
    close: function(){
      _.each(this.subViews, function(view) { view.remove(); });
      this.remove();
    }
  });
  return View;
})(int_app.View || {} , int_app.Model, int_app.Collection)
