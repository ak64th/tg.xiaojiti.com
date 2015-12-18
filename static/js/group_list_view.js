// GroupListView
int_app.View = (function(View, Model){
  View.GroupListView = GroupListView = Backbone.View.extend({
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
      data = { title: this.$('#group_add_title').val(), leader: this.wxUser.id };
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

  return View;
})(int_app.View || {} , int_app.Model)
