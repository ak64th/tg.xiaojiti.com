// ProductListView
int_app.View = (function(View, Model, Collection){
  View.ProductView = Backbone.View.extend({
    tagName: 'div',
    className: "goods-item clear",
    events: {
      "focus .editable":            "editing",
      "blur .editing":              "update",
      "click .cover":               "changingCover",
      'change input[name="photo"]': "changeCover",
      "click .trash":               "removeItem"
    },
    initialize: function () {
      this.listenTo(this.model, 'change', this.render);
      this.listenTo(this.model, 'destroy', this.remove);
    },
    template: JST.product,
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
    },
    // 选择图片
    changingCover: function(){
      this.$('input[name="photo"]').click();
    },
    // 先预览并检测图片，再上传图片
    changeCover: function(ev){
      var file = ev.currentTarget.files[0];
      var image = this.$('.cover')[0];
      var limit = 10;  //限制图片大小，单位MB
      var allowedTypes = ['JPG','JPEG','PNG','GIF','SVG','BMP','WEBP'];
      var imageType = /image.*/;

      detectDevice = function (){
        var ua = navigator.userAgent;
        var brand = {
          apple: ua.match(/(iPhone|iPod|iPad)/),
          android: ua.match(/Android/),
          microsoft: ua.match(/Windows Phone/)
        }
        return brand;
      };
      var device = detectDevice();

      if (!device.android){ // Since android doesn't handle file types right, do not do this check for phones
        if (!file.type.match(imageType)) {
          console.log('Unsupported format: ' + file.type);
          return false;
        }
      };

      var self = this;

      var updateFile = function(){
        var data = new FormData();
        data.append('photo', file);
        $.ajax({
          url: '/upload_photo/',
          data: data,
          cache: false,
          contentType: false,
          processData: false,
          type: 'POST',
          success: function(data){
            self.model.set('photo', data['filename']);
            self.model.save();
          },
          error: function(data){
            console.log('fail to upload photo');
          }
        });
      };

      var reader = new FileReader();
      reader.onload = function(e) {
        var format = e.target.result.split(';');
        format = format[0].split('/');
          format = format[1].split('+');
        format = format[0].toUpperCase();

        // We will change this for an android
        if (device.android){
          format = file.name.split('.');
              format = format[format.length-1].split('+');
          format = format[0].toUpperCase();
        }

        if (allowedTypes.indexOf(format)>=0 && e.total<(limit*1024*1024)){
          image.src = e.target.result;
          updateFile();
        }
      };

      reader.readAsDataURL(file);
    },
    removeItem: function(){
      this.model.destroy();
    }
  });

  View.ProductListView = Backbone.View.extend({
    tagName: "div",
    id: "group_detail_container",
    className: "goods-list",
    buttons: {
      'add': $('<a class="btn1 new"></a>'),
      'submit': $('<a class="btn2 submit"></a>'),
      'statistic': $('<a class="btn3 summary"></a>'),
      'finish': $('<a class="btn4"></a>'),
    },
    events: {
      "click .new": "newProduct",
      "click .submit": "submitGroup",
      "click .summary": "groupSummary",
    },
    initialize: function(options) {
      this.initUI();
      this.group_id = options.group_id;
      this.collection = new Collection.ProductList();
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
    },
    groupSummary: function(){
      window.location.hash = '/group/' + this.group_id + '/summary/';
    }
  });

  return View;
})(int_app.View || {} , int_app.Model, int_app.Collection)
