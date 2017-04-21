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

    template: _.template($('#git-tmpl').html()),

    initialize: function() {
        this.model.on('change', this.render, this);
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },

    events: {
        'click .specificCommit a': 'toggleCommitDetails'
    },

    toggleCommitDetails: function(e) {
        // Don't change scroll position even if href begins with the hash symbol #.
        e.preventDefault();

        $(e.target.parentElement).find(".tableParent").first().slideToggle("slow");

        // Don't change scroll position even if href begins with the hash symbol #.
        return false;
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