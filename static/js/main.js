// 模块1
var int_app = (function(int_app){
  int_app.Model = int_app.Model || {}
  int_app.Model.BaseModel = BaseModel = Backbone.Model.extend({
    // Add trailing slash after url
    url: function() {
      var origUrl = Backbone.Model.prototype.url.call(this);
      return origUrl + ((origUrl.length > 0 && origUrl.charAt(origUrl.length - 1) === '/') ? '' : '/');
    },
    // parse tastypie style restful response
    parse: function(data) {
      return data && data.objects && (_.isArray(data.objects) ? data.objects[0] : data.objects) || data;
    },
    //exclude some fields
    excludedFields: ['created','modified'],
    sync: function(method, model, options) {
      if ( method === 'create' || method === 'update'  ) {
          var notSync = model.excludedFields;
          if (notSync) {
              options.attrs = options.attrs || model.toJSON();
              // Use notSync either as an array or string
              if (Object.prototype.toString.call(notSync) !== '[object Array]') {
                  notSync = [ notSync ];
              }
              options.attrs = _.omit( options.attrs, notSync );
          }
      }

      Backbone.Model.prototype.sync.call(this, method, model, options);
    }
  });

  int_app.Collection = int_app.Collection || {}
  int_app.Collection.BaseCollection = Backbone.Collection.extend({
    parse: function(data) {
      if (data && data.meta) {
        this.meta = data.meta;
      }
      return data && data.objects || data;
    }
  });

  int_app.Model.GroupModel = int_app.Model.BaseModel.extend({

    defaults: function() {
      return {
        title: "No title",
        "content": "No content yet",
        "leader": 0
      };
    },

    initialize: function() {},
    urlRoot: function() {
      return '/api/v1/group/';
    },
  });

  int_app.Collection.GroupList = GroupList = int_app.Collection.BaseCollection.extend({
    model: int_app.Model.GroupModel,
    url: '/api/v1/group/',
  });


  int_app.Model.ProductModel = int_app.Model.BaseModel.extend({

    defaults: function() {
      return {
        "title": "商品标题",
        "price": 10,
        "content": "商品介绍"
      }
    },
    urlRoot: function() {
      return '/api/v1/product/';
    },
  });

  int_app.Collection.ProductList = int_app.Collection.BaseCollection.extend({
    model: int_app.Model.ProductModel,
    url: '/api/v1/product/',
  });

  int_app.Model.WxUserModel = int_app.Model.BaseModel.extend({
    urlRoot: function() {
      return '/api/v1/wxuser/';
    }
  });

  return int_app;
})( window.int_app || {} );


//模块2
var int_app = (function(int_app){
  int_app.View = int_app.View || {};

  int_app.View.GroupListView = GroupListView = Backbone.View.extend({
    el: $('#group_view_container'),
    initialize: function(options) {
      this.wxUser = options && options.wxUser || {};
      this.collection = new int_app.Collection.GroupList();
      this.template = _.template($('#group_list_template').html());
      this.listContainer = this.$('#group_list_container');
      this.listContainerCount = 0;
      this.listenTo(this.collection, 'add', this.onModelAdd);
      this.loadGroups();
    },
    events: {
      'click #group_add': 'create_group_pop',
      'click #group_add_cancel': 'create_group_pop_cancel',
      'click #group_add_submit': 'create_group_pop_submit'
    },
    render: function() {
      this.$el.show();
      return this;
    },
    close: function() {
      this.$el.hide();
      return this;
    },
    loadGroups: function(){
      data = this.wxUser ?  {leader: this.wxUser.id} : {};
      this.collection.fetch({ data: data });
    },
    // 显示单个group，index表示这是当前显示的第几个group
    renderOne: function(group, index){
      var renderedContent = this.template({
        group: group,
        index: index
      });
      this.listContainer.append(renderedContent);
    },
    onModelAdd: function(group) {
      this.renderOne(group.toJSON(), this.listContainerCount++);
    },
    create_group_pop: function(){
      this.$('#modal-container').show();
    },
    create_group_pop_cancel: function(){
      this.$('#modal-container').hide();
    },
    create_group_pop_submit: function(){
      data = { title: this.$('#group_add_title').val(), content: "", leader: this.wxUser.id };
      this.collection.create(data, {
        wait: true,
        success : function(model, resp, options){
          console.log('success callback');
          console.log(model);
          location.hash = '/group/' + model.get('id') + '/';
        },
        error : function(err) {
          console.log('error callback');
          console.log(err);
        }
      });
      this.$('#modal-container').hide();
    }
  });

  int_app.View.ProductView = Backbone.View.extend({
    tagName: 'div',
    className: "goods-item clear",
    events: {
      "focus .editable": "editing",
      "blur .editing": "update",
    },
    initialize: function () {
      this.listenTo(this.model, 'change', this.render);
      this.listenTo(this.model, 'destroy', this.remove);
    },
    template: _.template($('#product_template').html()),
    render: function(){
      this.$el.html(this.template({product: this.model.toJSON()}));
      return this;
    },
    editing: function(ev){
      console.log('editing');
      $(ev.currentTarget).addClass('editing');
    },
    update: function(ev){
      console.log('update');
      $target = $(ev.currentTarget)
      field = $target.data('field');
      value = $target.val();
      this.model.set(field, value)
      if (this.model.hasChanged(field)){
        this.model.save();
      }
      $target.removeClass('editing');
    }
  });

  int_app.View.ProductListView = Backbone.View.extend({
    tagName: "div",
    id: "group_detail_container",
    className: "goods-list",
    buttons: {
      'add': $('<a class="btn1 new"></a>'),
      'submit': $('<a class="btn2 submit"></a>'),
      'statistic': $('<a class="btn3"></a>'),
      'finish': $('<a class="btn4"></a>'),
    },
    events: {
      "click .new": "newProduct",
      "click .submit": "submitGroup",
    },
    initialize: function(options) {
      this.initUI();
      this.group_id = options.group_id;
      this.collection = new int_app.Collection.ProductList();
      this.subViews = [];
      this.listenTo(this.collection, "reset", this.resetAll);
      this.listenTo(this.collection, 'add', this.addOne);
      this.collection.fetch({ data: { group: this.group_id } });
    },
    initUI: function(){
      this.$el.html('');
      $buttons = $('<div class="goods-list-btns">');
      _.each(this.buttons, function(button) { $buttons.append(button); });
      this.$el.append($buttons);
    },
    render: function() {
      $("body").append(this.el);
    },
    addOne: function(product){
      view = new int_app.View.ProductView({model: product});
      this.subViews.push(view);
      this.$('div.goods-list-btns').before(view.render().el);
    },
    resetAll: function(){
      _.each(this.subViews, function(view) { view.remove(); });
      this.subViews = [];
      this.initUI();
      this.collection.each(this.addOne, this);
    },
    close: function(){
      _.each(this.subViews, function(view) { view.remove(); });
      this.remove();
    },
    newProduct: function(){
      product = new this.collection.model({'group': this.group_id});
      this.collection.add(product);
    },
    submitGroup: function(){
      location.hash = '/group/';
    }
  });
  return int_app;
})( int_app );
