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
    tagName: 'div',
    className: '',

    template: _.template($('#todo-tmpl').html()),

    initialize: function() {
        this.model.on('change', this.render, this);
    },

    render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    }
});

var AppointmentListView = Backbone.View.extend({
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
        var appointmentView = new AppointmentView({
            model: model,
            collection: this.collection
        });
        this.$el.append(appointmentView.render().el);
    }
});

//--------------
// Gath model
//--------------
var appointments = new AppointmentList();
appointments.fetch();

var appointmentListView = new AppointmentListView({
    collection: appointments
});

//--------------
// Attach markup
//--------------
$('#app').html(appointmentListView.el);