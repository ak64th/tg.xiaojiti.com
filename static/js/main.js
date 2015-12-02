var _sync = Backbone.sync;
Backbone.sync = function(method, model, options) {

  // Add trailing slash to backbone model views
  var _url = _.isFunction(model.url) ? model.url() : model.url;
  _url = addSlash(_url);

  options = _.extend(options, {
    url: _url
  });

  return _sync(method, model, options);
};

var addSlash = function(str) {
  return str + ((str.length > 0 && str.charAt(str.length - 1) === '/') ? '' : '/');
};

Backbone.Model.prototype.parse = function(data) {
  return data && data.objects && (_.isArray(data.objects) ? data.objects[0] : data.objects) || data;
};

Backbone.Collection.prototype.parse = function(data) {
  if (data && data.meta) {
    this.meta = data.meta;
  }
  return data && data.objects || data;
};

get_openid = function() {
  return 'ba39kz15abg2';
}


var GroupModel = Backbone.Model.extend({

  defaults: function() {
    return {
      title: "Empty Group",
      "content": "No content yet",
      "leader": 0
    };
  },

  initialize: function() {},
  urlRoot: function() {
    return '/api/v1/group/';
  },
});


var GroupList = Backbone.Collection.extend({
  model: GroupModel,
  url: '/api/v1/group/',
});


var GroupListView = Backbone.View.extend({
  el: $('#group_view_container'),
  initialize: function() {
    var self = this;
    this.collection = new GroupList;
    this.template = _.template($('#group_list_template').html());
    this.listContainer = this.$('#group_list_container');
    this.listContainerCount = 0;
    this.collection.fetch({
      data: {leader__openid: get_openid()}
    }).done(function(){
      self.render();
      self.listenTo(self.collection, 'add', self.onModelAdd);
    });
  },
  // 显示单个group，index表示这是当前显示的第几个group
  renderOne: function(group, index){
    var renderedContent = this.template({
      group: group,
      index: index
    });
    this.listContainer.append(renderedContent);
  },
  render: function() {
    var self = this;
    _.each(self.collection.toJSON(), function(group, index) {
      self.renderOne(group,index);
    });
  },
  onModelAdd: function(group) {
    this.renderOne(group.toJSON(), this.listContainerCount++);
  }
});

groupView = new GroupListView
