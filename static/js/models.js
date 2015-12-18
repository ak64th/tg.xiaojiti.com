// 模块1
var int_app = window.int_app || {}

int_app.Model = (function(Model){

  Model.BaseModel = BaseModel = Backbone.Model.extend({
    // Add trailing slash after url
    url: function() {
      var origUrl = Backbone.Model.prototype.url.call(this);
      return origUrl + ((origUrl.length > 0 && origUrl.charAt(origUrl.length - 1) === '/') ? '' : '/');
    },
    // parse tastypie style restful response
    parse: function(data) {
      //return data && data.objects && (_.isArray(data.objects) ? data.objects[0] : data.objects) || data;
      if (data && data.objects && _.isArray(data.objects)){
        return data.objects[0] || {};
      }
      return data;
    },
    //exclude some fields
    excludedFields: ['created','modified'],

    //internal attributes hash after last sync
    lastSyncAttributes: {},

    hasChangedSinceLastSync: function(){
      currentAttributes = _.clone(this.attributes);
      return JSON.stringify(currentAttributes) != JSON.stringify(this.lastSyncAttributes);
    },

    sync: function(method, model, options) {
      var notSync = model.excludedFields;

      options = options || {};
      var success = options.success;
      options.success = function(resp) {
        success && success(resp);
        model.lastSyncAttributes = _.clone(model.attributes);
      };

      if (notSync) {
        if ( method === 'create' || method === 'update'  ) {
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

  Model.GroupModel = Model.BaseModel.extend({

    defaults: function() {
      return {
        title: ""
      };
    },

    initialize: function() {},
    urlRoot: function() {
      return '/api/v1/group/';
    },
  });;


  Model.ProductModel = Model.BaseModel.extend({

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

  Model.WxUserModel = Model.BaseModel.extend({
    urlRoot: function() {
      return '/api/v1/wxuser/';
    }
  });

  Model.PurchaseModel = Model.BaseModel.extend({
    excludedFields: ['created','modified','checked'],
    urlRoot: function() {
      return '/api/v1/purchase/';
    }
  });

  return Model;
})( int_app.Model || {} );


int_app.Collection = (function(Collection, Model){

  Collection.BaseCollection = Backbone.Collection.extend({
    parse: function(data) {
      if (data && data.meta) {
        this.meta = data.meta;
      }
      return data && data.objects || data;
    }
  });

  Collection.GroupList = GroupList = Collection.BaseCollection.extend({
    model: Model.GroupModel,
    url: '/api/v1/group/',
  });


  Collection.ProductList = Collection.BaseCollection.extend({
    model: Model.ProductModel,
    url: '/api/v1/product/',
  });

  Collection.WxUserList = Collection.BaseCollection.extend({
    model: Model.WxUserModel,
    url: '/api/v1/wxuser/',
  });

  Collection.PurchaseList = Collection.BaseCollection.extend({
    model: Model.PurchaseModel,
    url: '/api/v1/purchase/',
  });

  return Collection;
})( int_app.Collection || {}, int_app.Model );