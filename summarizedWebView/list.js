'use strict';

//--------------
// Models
//--------------
var Remote = Backbone.Model.extend();

//--------------
// Collections
//--------------
var RemoteList = Backbone.Collection.extend({
    url: 'example2b.json',
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
        'click .specificCommit a': 'toggleTable',
    },

    toggleTable: function(e) {
        // Don't change scroll position even if href begins with the hash symbol #.
        e.preventDefault();

        var tableClass = $(e.target).data("table");
        $(e.target.parentElement).find(tableClass).first().slideToggle("slow");

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

/*todo:
    top filter
        separate model,view for filters
        organization (count): all (x), edx (y), etc (z). -> sorted by totals
        show all collections,just collections with differences

    diff
        sort by commit date
        radio buttons -> link

    UX branch,tag count header
        model values -> array
        reconstruct header string, toggle prefix based on count
        hyperlink full github urls: tags,branch (new tab)

    validate all code path before merge
        test nmap installer on 14,16

    reach
        type tag (rows will/hide show based on filter)
            autocomplete
        real webApp,deployment
            model ingestion (form upload,scp,email)
*/