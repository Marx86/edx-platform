define(
    [
        'jquery',
        'underscore',
        'backbone',
        'js/views/previous_video_upload',
        'common/js/spec_helpers/template_helpers',
        'common/js/spec_helpers/view_helpers',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'mock-ajax'
    ],
    function($, _, Backbone, PreviousVideoUploadView, TemplateHelpers, ViewHelpers, AjaxHelpers) {
        'use strict';
        describe('PreviousVideoUploadView', function() {
            var previousVideoUploadView = function(modelData) {
                var defaultData = {
                        client_video_id: 'foo.mp4',
                        duration: 42,
                        created: '2014-11-25T23:13:05',
                        edx_video_id: 'dummy_id',
                        status: 'uploading',
                        status_value: ''
                    },
                    viewItem = new PreviousVideoUploadView({
                        model: new Backbone.Model($.extend({}, defaultData, modelData)),
                        videoHandlerUrl: '/videos/course-v1:org.0+course_0+Run_0'
                    });
                return viewItem;
            };
            var render = function(modelData) {
                var view = previousVideoUploadView(modelData);
                return view.render().$el;
            };

            beforeEach(function() {
                setFixtures('<div id="page-prompt"></div><div id="page-notification"></div>');
                TemplateHelpers.installTemplate('previous-video-upload', false);
                jasmine.Ajax.install();
            });

            afterEach(function() {
                jasmine.Ajax.uninstall();
            });

            it('should render video name correctly', function() {
                var testName = 'test name';
                var $el = render({client_video_id: testName});
                expect($el.find('.name-col>span').text()).toEqual(testName);
            });

            it('called checkStatusVideo if video status is in_progress and storage is equal to azure',
                function() {
                    var view = previousVideoUploadView({status_value: 'transcode_active'});
                    view.storageService = 'azure';
                    view.checkStatusVideo = jasmine.createSpy();

                    view.render();

                    expect(view.checkStatusVideo).toHaveBeenCalled();
                }
            );

            it('should render correct new video status',
                function() {
                    var requests,
                        view = previousVideoUploadView({status_value: 'transcode_active'});
                    view.storageService = 'azure';
                    view.render();

                    jasmine.Ajax.uninstall();
                    jasmine.clock().install();

                    requests = AjaxHelpers.requests(this);
                    view.checkStatusVideo();

                    jasmine.clock().tick(20000);

                    AjaxHelpers.respond(requests, {
                        status: 200,
                        body: {
                            videos: [
                                {
                                    status: 'Ready',
                                    created: '2018-02-06T11:03:22.421Z',
                                    client_video_id: 'video.mp4',
                                    status_value: 'file_complete',
                                    duration: 10.0,
                                    edx_video_id: 'dummy_id_1'
                                },
                                {
                                    status: 'Test status',
                                    created: '2018-02-06T10:57:20.997Z',
                                    client_video_id: 'TEST.mp4',
                                    status_value: 'test_status',
                                    duration: 20.0,
                                    edx_video_id: 'dummy_id'
                                }
                            ]
                        }
                    });

                    expect(view.$('.status-col').text().trim()).toEqual('Test status');
                    jasmine.clock().uninstall();
                    jasmine.Ajax.install();
                }
            );

            it('called renderTranscripts if video status is equal to file_complete and storage is equal to azure',
                function() {
                    var view = previousVideoUploadView({status_value: 'file_complete'});
                    view.storageService = 'azure';
                    view.renderTranscripts = jasmine.createSpy();

                    view.render();

                    expect(view.renderTranscripts).toHaveBeenCalled();
                }
            );

            it('should render transcripts video info', function() {
                var view = previousVideoUploadView({});
                view.transcriptsCollection = new Backbone.Collection([
                    {
                        name: 'transcript1.vtt',
                        language: 'en'
                    },
                    {
                        name: 'transcript2.vtt',
                        language: 'fr'
                    }
                ]);

                view.renderTranscripts();

                expect(view.transcriptsView.$('.js-transcript-container div.transcript-view').length).toEqual(2);
                expect(
                    view.transcriptsView.$('.js-transcript-container div.transcript-view:first div').text().trim()
                ).toEqual('transcript1.vtt (en)');
                expect(
                    view.transcriptsView.$('.js-transcript-container div.transcript-view:last div').text().trim()
                ).toEqual('transcript2.vtt (fr)');
            });

            it('should render correct link for transcripts adding', function() {
                var view = previousVideoUploadView({status_value: 'file_complete'});
                view.storageService = 'azure';
                view.render();

                expect(view.$('.js-add-transcript').length).toEqual(1);
            });

            it('should render correct link for transcripts toggle', function() {
                var view = previousVideoUploadView({status_value: 'file_complete'});
                view.storageService = 'azure';
                view.transcriptsCollection = new Backbone.Collection([
                    {
                        name: 'transcript1.vtt',
                        language: 'en'
                    },
                    {
                        name: 'transcript2.vtt',
                        language: 'fr'
                    }
                ]);
                view.render();

                expect(view.$('.js-toggle-transcripts').length).toEqual(1);
            });

            _.each(
                [
                    {desc: 'zero as pending', seconds: 0, expected: 'Pending'},
                    {desc: 'less than one second as zero', seconds: 0.75, expected: '0:00'},
                    {desc: 'with minutes and without seconds', seconds: 900, expected: '15:00'},
                    {desc: 'with seconds and without minutes', seconds: 15, expected: '0:15'},
                    {desc: 'with minutes and seconds', seconds: 915, expected: '15:15'},
                    {desc: 'with seconds padded', seconds: 5, expected: '0:05'},
                    {desc: 'longer than an hour as many minutes', seconds: 7425, expected: '123:45'}
                ],
                function(caseInfo) {
                    it('should render duration ' + caseInfo.desc, function() {
                        var $el = render({duration: caseInfo.seconds});
                        expect($el.find('.duration-col').text()).toEqual(caseInfo.expected);
                    });
                }
            );

            it('should render created timestamp correctly', function() {
                var fakeDate = 'fake formatted date';
                spyOn(Date.prototype, 'toLocaleString').and.callFake(
                    function(locales, options) {
                        expect(locales).toEqual([]);
                        expect(options.timeZone).toEqual('UTC');
                        expect(options.timeZoneName).toEqual('short');
                        return fakeDate;
                    }
                );
                var $el = render({});
                expect($el.find('.date-col').text()).toEqual(fakeDate);
            });

            it('should render video id correctly', function() {
                var testId = 'test_id';
                var $el = render({edx_video_id: testId});
                expect($el.find('.video-id-col').text()).toEqual(testId);
            });

            it('should render status correctly', function() {
                var testStatus = 'Test Status';
                var $el = render({status: testStatus});
                expect($el.find('.status-col').text()).toEqual(testStatus);
            });

            it('should render remove button correctly', function() {
                var $el = render(),
                    removeButton = $el.find('.actions-list .action-remove a.remove-video-button');

                expect(removeButton.data('tooltip')).toEqual('Remove this video');
                expect(removeButton.find('.sr').text()).toEqual('Remove foo.mp4 video');
            });

            it('shows a confirmation popup when the remove button is clicked', function() {
                var $el = render();
                $el.find('a.remove-video-button').click();
                expect($('.prompt.warning .title').text()).toEqual('Are you sure you want to remove this video from the list?');  // eslint-disable-line max-len
                expect(
                    $('.prompt.warning .message').text()
                ).toEqual(
                    'Removing a video from this list does not affect course content. Any content that uses a previously uploaded video ID continues to display in the course.'  // eslint-disable-line max-len
                );
                expect($('.prompt.warning .action-primary').text()).toEqual('Remove');
                expect($('.prompt.warning .action-secondary').text()).toEqual('Cancel');
            });

            it('shows a notification when the remove button is clicked', function() {
                var notificationSpy = ViewHelpers.createNotificationSpy(),
                    $el = render();
                $el.find('a.remove-video-button').click();
                $('.action-primary').click();
                ViewHelpers.verifyNotificationShowing(notificationSpy, /Removing/);
            });

            it('should render encrypt button correctly', function() {
                var view, $el, lockButton;
                view = previousVideoUploadView();
                view.storageService = 'azure';
                $el = view.render().$el;
                lockButton = $el.find('.js-lock-unlock-file');
                expect(lockButton.length).toEqual(0);

                view = previousVideoUploadView({status_value: 'file_complete'});
                view.storageService = 'azure';
                $el = view.render().$el;
                lockButton = $el.find('.js-lock-unlock-file');
                expect(lockButton.length).toEqual(1);
                expect(lockButton.hasClass('encrypted')).toBe(false);

                view = previousVideoUploadView({status_value: 'file_encrypted'});
                view.storageService = 'azure';
                $el = view.render().$el;
                lockButton = $el.find('.js-lock-unlock-file');
                expect(lockButton.length).toEqual(1);
                expect(lockButton.hasClass('encrypted')).toBe(true);
            });

            it('shows a confirmation popup when the encrypt button is clicked', function() {
                var view, $el;
                view = previousVideoUploadView({status_value: 'file_complete'});
                view.storageService = 'azure';
                $el = view.render().$el;
                $el.find('.js-lock-unlock-file').click();

                expect($('.prompt.warning .title').text()).toEqual('Are you sure you want to add encryption to this video file?');  // eslint-disable-line max-len
                expect(
                    $('.prompt.warning .message').text()
                ).toEqual(
                    'If the current video file is used in "Azure-media-service" xBlock, please go to the xBlock and redefine the video file.'  // eslint-disable-line max-len
                );
                expect($('.prompt.warning .action-primary').text()).toEqual('OK');
                expect($('.prompt.warning .action-secondary').text()).toEqual('Cancel');
            });
        });
    }
);
