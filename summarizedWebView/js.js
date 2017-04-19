'use strict';

//--------------
// Models
//--------------
var Remote = Backbone.Model.extend();

//--------------
// Collections
//--------------
var RemoteList = Backbone.Collection.extend({
    url: 'example.json',
    model: Remote,
    parse: function(response, options) {
        return response;
    }
});

//--------------
// Views
//--------------
var RemoteView = Backbone.View.extend({
    tagName: 'div',
    className: 'alternateBG',

    template: _.template($('#todo-tmpl').html()),

    initialize: function() {
        this.model.on('change', this.render, this);
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    }
});

var RemoteListView = Backbone.View.extend({
    tagName: 'div',
    className: '',

    initialize: function() {
        this.collection.on('sync', this.render, this);
    },

    render: function() {
        this.collection.forEach(this.addOne, this);
        return this;
    },

    addOne: function(model) {
        var remoteView = new RemoteView({
            model: model
        });
        this.$el.append(remoteView.render().el);
    }
});

//--------------
// Gath model
//--------------
var remotes = new RemoteList();
remotes.fetch();

var remoteListView = new RemoteListView({
    collection: remotes
});

//--------------
// Attach markup
//--------------
$('#app').html(remoteListView.el);