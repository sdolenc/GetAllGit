'use strict';

//--------------
// Models
//--------------
var Appointment = Backbone.Model.extend();

//--------------
// Collections
//--------------
var AppointmentList = Backbone.Collection.extend({
    url: 'example.json',
    model: Appointment
});

//--------------
// Views
//--------------
var AppointmentView = Backbone.View.extend({
    tagName: 'li',
    className: 'todo',

    template: _.template($('#todo-tmpl').html()),

    initialize: function() {
        this.model.on('change', this.render, this);
        this.model.on('remove', this.remove, this);
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },

    toggleComplete: function() {
        this.model.set({ complete: !this.model.get("complete") });
    },

    cancel: function() {
        this.model.set({ canceled: true });
        this.collection.remove(this.model);
    }
});

var AppointmentListView = Backbone.View.extend({
    tagName: 'ul',
    className: 'todos',

    initialize: function() {
        this.collection.on('sync', this.render, this);
    },

    render: function() {
        this.collection.forEach(this.addOne, this);
        return this;
    },

    addOne: function(model) {
        var appointmentView = new AppointmentView({
            model: model,
            collection: this.collection
        });
        this.$el.append(appointmentView.render().el);
    },

    remove: function() {
        this.$el.remove();
    }
});


var appointments = new AppointmentList();
appointments.fetch();

var appointmentListView = new AppointmentListView({
    collection: appointments
});

$('#app').html(appointmentListView.el);