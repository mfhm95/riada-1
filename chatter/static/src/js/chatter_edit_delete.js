odoo.define('chatter.widget.Thread', function (require) {
    "use strict";

    var ThreadWidget = require('mail.widget.Thread');
    var framework = require('web.framework');
    var Activity = require('mail.Activity');
    var field_registry = require('web.field_registry');
    var KanbanActivity = field_registry.get('kanban_activity');
    var time = require('web.time');
    var mailUtils = require('mail.utils');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var session = require('web.session');
    var config = require('web.config');
    var Message = require('mail.model.Message');
    var Chatter = require('mail.Chatter');
//    var ActivityMenu = require('mail.systray.ActivityMenu');
    var QWeb = core.qweb;
    var _t = core._t;

    Message.include({
        init: function () {
            this._super.apply(this, arguments);
            this._getCurrentUser = arguments[1].current_user;
        },

        getCurrentUser: function(){
            return this._getCurrentUser;
        },
    });

    // helper method for labelling
    var setDelayLabel = function (activities){
        var today = moment();
        _.each(activities, function (activity){
            var toDisplay = '';
            var diff = activity.datetime_deadline.diff(today, 'days', true); // true means no rounding
            var diff_hours = activity.datetime_deadline.diff(today, 'hours', true); // true means no rounding
            var diff_hour = diff_hours % 24;

            if (diff === 0){
                toDisplay = _t("Today");
            } else {
                if (diff < 0){ // overdue
                    if (diff === -1){
                        toDisplay = _t("Yesterday");
                    } else {
                        if(!diff_hour)
                            toDisplay = _.str.sprintf(_t("%d days overdue"), Math.abs(diff));
                        else
                            toDisplay = _.str.sprintf(_t("%d days and %d hours overdue"), Math.abs(diff), Math.abs(diff_hour));
                    }
                } else { // due
                    if (diff === 1){
                        toDisplay = _t("Tomorrow");
                    } else {
                        toDisplay = _.str.sprintf(_t("Due in %d days and %d hours"), Math.abs(diff),Math.abs(diff_hour));
                    }
                }
            }
            activity.label_delay = toDisplay;
        });
        return activities;
    };

    var setFileUploadID = function (activities) {
    _.each(activities, function (activity) {
        if (activity.activity_category === 'upload_file') {
            activity.fileuploadID = _.uniqueId('o_fileupload');
        }
    });
    return activities;
};

    function _readActivities(self, ids) {

        if (!ids.length) {
            return Promise.resolve([]);
        }
        var context = self.getSession().user_context;
        if (self.record && !_.isEmpty(self.record.getContext())) {
            context = self.record.getContext();
        }
        return self._rpc({
            model: 'mail.activity',
            method: 'activity_format',
            args: [ids],
            context: context,
        }).then(function (activities) {
            // convert create_date and date_deadline to moments
            _.each(activities, function (activity) {
                activity.create_date = moment(time.auto_str_to_date(activity.create_date));
                activity.date_deadline = moment(time.auto_str_to_date(activity.date_deadline));
                activity.datetime_deadline = moment(time.auto_str_to_date(activity.datetime_deadline));
            });
             // sort activities by due date
            activities = _.sortBy(activities, 'datetime_deadline');
            return activities;
    });
}

    ThreadWidget.include({
        events: _.extend({}, ThreadWidget.prototype.events, {
            'click .chatter_edit': 'chatter_edit',
            'click .chatter_delete': 'chatter_delete',
        }),
        /**
         * @override
         */

        render: function (thread, options) {
            var self = this;
            options.is_system = odoo.session_info.is_system;
            options.is_admin = odoo.session_info.is_admin
            self._super(thread, options);
        },


        chatter_edit: function (event) {
            var self = this;
            var id = $(event.target).data().messageId;

            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mail.message',
                view_id: 'view_message_chatter_form',
                views: [
                    [false, 'form']
                ],
                target: 'new',
                res_id: id,
            },{
                on_close: () => {
                    self.do_action({
                        type: 'ir.actions.client',
                        tag: 'reload',
                    })
                },
            });
        },

        chatter_delete: function (event) {
            var self = this;

            Dialog.alert(self, _t("Are you Sure you want to delete the log."), {
                title: _t("Delete Log"),
                confirm_callback: function() {
                    self._rpc({
                        model: 'mail.message',
                        method: 'unlink',
                        args: [$(event.target).data().messageId],
                    }).then(function(is_delete) {
                        if(is_delete) {
                            window.location.reload();
                        }
                    });
                },
            });
        },
    });

    Activity.include({
        events: _.extend({}, Activity.prototype.events, {
            'click .add_attachments': 'addAttachments',

        }),


        init: function() {
            var self = this;
            self._super.apply(this, arguments);
            self.sort_activities();
        },
        addAttachments: function(event){
            event.preventDefault();
            var self = this;
            var id = $(event.target).data().activityId;
            var action = {
                type: 'ir.actions.act_window',
                name: _t("Schedule Activity"),
                res_model: 'mail.activity.attachments',
                views: [[false, 'form']],
                view_id: 'chatter.view_mail_activity_attachment_form2',
                target: 'new',
                context: {
                    default_res_id: self.res_id,
                    default_res_model: self.model,
                    default_res_activity_id: id,
                },

            };
            return self.do_action(action, {
                on_close: self._reload.bind(self, { activity: true, thread: true })

            });
        },



//        addAttachments: function(event){
//            event.preventDefault();
//            var id = $(event.target).data().activityId;
//            var action = {
//                type: 'ir.actions.act_window',
//                name: _t("Schedule Activity"),
//                res_model: 'mail.activity.attachments',
//                views: [[false, 'form']],
//                view_id: 'view_mail_activity_attachment_form2',
//                target: 'new',
//                context: {
//                    default_res_id: self.res_id,
//                    default_res_model: self.model,
//                },
//            };
//            return this.do_action(action, {
//                on_close: this._reload.bind(this, { activity: true, thread: true })
//
//            });
//
//
//        },

        sort_activities: function(){

            if( this._activities.length && typeof(this._activities[0].datetime_deadline) != "object"){

                this._activities =  _.each(this._activities, function (activity) {
                    activity.datetime_deadline = moment(time.auto_str_to_date(activity.datetime_deadline));
                });
            }

            // sort activities by due date
            this._activities = _.sortBy(this._activities, 'datetime_deadline');
        },

        _render: function () {
            _.each(this._activities, function (activity) {
                var note = mailUtils.parseAndTransform(activity.note || '', mailUtils.inline);
                var is_blank = (/^\s*$/).test(note);
                if (!is_blank) {
                    activity.note = mailUtils.parseAndTransform(activity.note, mailUtils.addLink);
                } else {
                    activity.note = '';
                }
            });

            this.sort_activities();

            var activities = setFileUploadID(setDelayLabel(this._activities));
            if (activities.length) {
                var nbActivities = _.countBy(activities, 'state');
                this.$el.html(QWeb.render('mail.activity_items', {
                    uid: session.uid,
                    activities: activities,
                    nbPlannedActivities: nbActivities.planned,
                    nbTodayActivities: nbActivities.today,
                    nbOverdueActivities: nbActivities.overdue,
                    dateFormat: time.getLangDateFormat(),
                    datetimeFormat: time.getLangDatetimeFormat(),
                    session: session,
                    widget: this,
                }));
                this._bindOnUploadAction(this._activities);
            } else {
                this._unbindOnUploadAction(this._activities);
                this.$el.empty();
            }
        },
    });

    KanbanActivity.include({

        _renderDropdown: function () {
            var self = this;
            this.$('.o_activity')
                .toggleClass('dropdown-menu-right', config.device.isMobile)
                .html(QWeb.render('mail.KanbanActivityLoading'));
            return _readActivities(this, this.value.res_ids).then(function (activities) {
                activities = setFileUploadID(activities);
                self.$('.o_activity').html(QWeb.render('mail.KanbanActivityDropdown', {
                    selection: self.selection,
                    records: _.groupBy(setDelayLabel(activities), 'state'),
                    session: session,
                    widget: self,
                }));
                self._bindOnUploadAction(activities);
            });
        },
    })

    Chatter.include({

        start: function () {
            var self = this;
            var parent_super = self._super;
            session.user_has_group('chatter.message_to_customer_group').then((res) => {
                self.message_to_customer_group = res;
                parent_super.apply(self, arguments);
            })
        },

        _renderButtons: function () {
            return QWeb.render('mail.chatter.Buttons', {
                newMessageButton: !!this.fields.thread,
                logNoteButton: this.hasLogButton,
                scheduleActivityButton: !!this.fields.activity,
                isMobile: config.device.isMobile,
                is_message_to_customer: this.message_to_customer_group || false,
            });
        },

    })

})