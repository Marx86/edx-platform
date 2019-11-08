(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'logger',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_account/models/position_model',
        'js/student_account/views/account_settings_fields',
        'js/student_account/views/account_settings_view',
        'edx-ui-toolkit/js/utils/string-utils',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, $, _, Backbone, Logger, UserAccountModel, UserPreferencesModel, PositionAccountModel,
                 AccountSettingsFieldViews, AccountSettingsView, StringUtils, HtmlUtils) {
        return function(
            fieldsData,
            ordersHistoryData,
            authData,
            passwordResetSupportUrl,
            userAccountsApiUrl,
            userPreferencesApiUrl,
            accountUserId,
            platformName,
            contactEmail,
            allowEmailChange,
            socialPlatforms,
            syncLearnerProfileData,
            enterpriseName,
            enterpriseReadonlyAccountFields,
            edxSupportUrl,
            extendedProfileFields,
            displayAccountDeletion,
            positionAccountApiUrl,
            isProgressForm,
            listFormFields
        ) {
            var $accountSettingsElement, userAccountModel, userPreferencesModel, positionAccountModel, aboutSectionsData,
                accountsSectionData, ordersSectionData, accountSettingsView, showAccountSettingsPage,
                showLoadingError, orderNumber, getUserField, userFields, timeZoneDropdownField, countryDropdownField,
                emailFieldView, socialFields, accountDeletionFields, platformData,
                aboutSectionMessageType, aboutSectionMessage, fullnameFieldView, countryFieldView,
                fullNameFieldData, emailFieldData, countryFieldData, additionalFields, fieldItem;

            $accountSettingsElement = $('.wrapper-account-settings');

            userAccountModel = new UserAccountModel();
            userAccountModel.url = userAccountsApiUrl;

            userPreferencesModel = new UserPreferencesModel();
            userPreferencesModel.url = userPreferencesApiUrl;

            var persistChanges = !isProgressForm;

            if (syncLearnerProfileData && enterpriseName) {
                aboutSectionMessageType = 'info';
                aboutSectionMessage = HtmlUtils.interpolateHtml(
                    gettext('Your profile settings are managed by {enterprise_name}. Contact your administrator or {link_start}edX Support{link_end} for help.'),  // eslint-disable-line max-len
                    {
                        enterprise_name: enterpriseName,
                        link_start: HtmlUtils.HTML(
                            StringUtils.interpolate(
                                '<a href="{edx_support_url}">', {
                                    edx_support_url: edxSupportUrl
                                }
                            )
                        ),
                        link_end: HtmlUtils.HTML('</a>')
                    }
                );
            }

            emailFieldData = {
                model: userAccountModel,
                title: gettext('Email Address (Sign In)'),
                valueAttribute: 'email',
                helpMessage: StringUtils.interpolate(
                    gettext('You receive messages from {platform_name} and course teams at this address.'),  // eslint-disable-line max-len
                    {platform_name: platformName}
                ),
                persistChanges: true
            };
            if (!allowEmailChange || (syncLearnerProfileData && enterpriseReadonlyAccountFields.fields.indexOf('email') !== -1)) {  // eslint-disable-line max-len
                emailFieldView = {
                    view: new AccountSettingsFieldViews.ReadonlyFieldView(emailFieldData)
                };
            } else {
                emailFieldView = {
                    view: new AccountSettingsFieldViews.EmailFieldView(emailFieldData)
                };
            }

            fullNameFieldData = {
                model: userAccountModel,
                title: gettext('Full Name'),
                valueAttribute: 'name',
                helpMessage: gettext('The name that is used for ID verification and that appears on your certificates.'),  // eslint-disable-line max-len,
                persistChanges: persistChanges
            };
            if (syncLearnerProfileData && enterpriseReadonlyAccountFields.fields.indexOf('name') !== -1) {
                fullnameFieldView = {
                    view: new AccountSettingsFieldViews.ReadonlyFieldView(fullNameFieldData)
                };
            } else {
                fullnameFieldView = {
                    view: new AccountSettingsFieldViews.TextFieldView(fullNameFieldData)
                };
            }

            countryFieldData = {
                model: userAccountModel,
                required: true,
                title: gettext('Country or Region of Residence'),
                valueAttribute: 'country',
                options: fieldsData.country.options,
                persistChanges: persistChanges,
                helpMessage: gettext('The country or region where you live.')
            };
            if (syncLearnerProfileData && enterpriseReadonlyAccountFields.fields.indexOf('country') !== -1) {
                countryFieldData.editable = 'never';
                countryFieldView = {
                    view: new AccountSettingsFieldViews.DropdownFieldView(
                        countryFieldData
                    )
                };
            } else {
                countryFieldView = {
                    view: new AccountSettingsFieldViews.DropdownFieldView(countryFieldData)
                };
            }

            aboutSectionsData = [
                {
                    title: gettext('Basic Account Information'),
                    subtitle: gettext('These settings include basic information about your account.'),

                    messageType: aboutSectionMessageType,
                    message: aboutSectionMessage,

                    fields: [
                        {
                            view: new AccountSettingsFieldViews.ReadonlyFieldView({
                                model: userAccountModel,
                                title: gettext('Username'),
                                valueAttribute: 'username',
                                helpMessage: StringUtils.interpolate(
                                    gettext('The name that identifies you on {platform_name}. You cannot change your username.'),  // eslint-disable-line max-len
                                    {platform_name: platformName}
                                )
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView(
                                {
                                    model: userAccountModel,
                                    title: gettext('First Name'),
                                    valueAttribute: 'first_name',
                                    helpMessage: gettext('Add your first name.'),  // eslint-disable-line max-len,
                                    persistChanges: persistChanges
                                }
                            )
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Second Name'),
                                valueAttribute: 'second_name',
                                helpMessage: gettext('Add your second name.'),
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView(
                                {
                                    model: userAccountModel,
                                    title: gettext('Last Name'),
                                    valueAttribute: 'last_name',
                                    helpMessage: gettext('Add your last name.'),  // eslint-disable-line max-len,
                                    persistChanges: persistChanges
                                }
                            )
                        },
                        fullnameFieldView,
                        emailFieldView,
                        {
                            view: new AccountSettingsFieldViews.PasswordFieldView({
                                model: userAccountModel,
                                title: gettext('Password'),
                                screenReaderTitle: gettext('Reset Your Password'),
                                valueAttribute: 'password',
                                emailAttribute: 'email',
                                passwordResetSupportUrl: passwordResetSupportUrl,
                                linkTitle: gettext('Reset Your Password'),
                                linkHref: fieldsData.password.url,
                                helpMessage: gettext('Check your email account for instructions to reset your password.')  // eslint-disable-line max-len
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.LanguagePreferenceFieldView({
                                model: userPreferencesModel,
                                title: gettext('Language'),
                                valueAttribute: 'pref-lang',
                                required: true,
                                refreshPageOnSave: true,
                                helpMessage: StringUtils.interpolate(
                                    gettext('The language used throughout this site. This site is currently available in a limited number of languages. Changing the value of this field will cause the page to refresh.'),  // eslint-disable-line max-len
                                    {platform_name: platformName}
                                ),
                                options: fieldsData.language.options,
                                persistChanges: persistChanges
                            })
                        },
                        countryFieldView,
                        {
                            view: new AccountSettingsFieldViews.TimeZoneFieldView({
                                model: userPreferencesModel,
                                required: true,
                                title: gettext('Time Zone'),
                                valueAttribute: 'time_zone',
                                helpMessage: gettext('Select the time zone for displaying course dates. If you do not specify a time zone, course dates, including assignment deadlines, will be displayed in your browser\'s local time zone.'), // eslint-disable-line max-len
                                groupOptions: [{
                                    groupTitle: gettext('All Time Zones'),
                                    selectOptions: fieldsData.time_zone.options,
                                    nullValueOptionLabel: gettext('Default (Local Time Zone)')
                                }],
                                persistChanges: persistChanges
                            })
                        }
                    ]
                },
                {
                    title: gettext('Additional Information'),
                    fields: [
                        {
                            view: new AccountSettingsFieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Education Completed'),
                                valueAttribute: 'level_of_education',
                                options: fieldsData.level_of_education.options,
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Gender'),
                                valueAttribute: 'gender',
                                options: fieldsData.gender.options,
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Date of Birth'),
                                valueAttribute: 'date_of_birth',
                                helpMessage: gettext('Select your date of birth'),
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.LanguageProficienciesFieldView({
                                model: userAccountModel,
                                title: gettext('Preferred Language'),
                                valueAttribute: 'language_proficiencies',
                                options: fieldsData.preferred_language.options,
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Phone'),
                                valueAttribute: 'phone',
                                helpMessage: gettext('Phone number'),
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.TextFieldView({
                                model: userAccountModel,
                                title: gettext('Additional Email'),
                                valueAttribute: 'additional_email',
                                helpMessage: gettext('Add your additional Email.'),
                                persistChanges: persistChanges
                            })
                        },
                        {
                            view: new AccountSettingsFieldViews.DropdownFieldView({
                                model: userAccountModel,
                                title: gettext('Region'),
                                valueAttribute: 'region',
                                options: fieldsData.region.options,
                                helpMessage: gettext('The region where you live.'),
                                persistChanges: persistChanges
                            })
                        }
                    ]
                }
            ];


            var PositionAccountCollection = Backbone.Collection.extend({
                model: PositionAccountModel,
                url: positionAccountApiUrl
            });

            var positionAccountCollection = new PositionAccountCollection();

            positionAccountCollection.fetch({
                success: function(data) {
                    aboutSectionsData[1].fields.push({
                        view: new AccountSettingsFieldViews.EditableDualFieldView({
                            model: data.models[0],
                            title: gettext('Position'),
                            valueAttribute: 'position',
                            positionChoices: data.models[0].attributes.position.options,
                            helpMessage: gettext('Select type of your position.'),
                            helpMessageSubPosition: gettext('Select your position.'),
                            helpMessageSpecialization: gettext('Select your specialization.'),
                            persistChanges: true,
                        })
                    });
                    accountSettingsView.render();
                    // input mask for 'phone' field
                    $('#field-input-phone').inputmask("(999) 999 99 99");
                    // datepicker for 'date of birth' field
                    $('#field-input-date_of_birth').attr('autocomplete','off').datepicker({
                        format: 'yyyy-mm-dd',
                        autoHide: true,
                        endDate: new Date()
                    });
                },
                error: showLoadingError
            });


            // Add the extended profile fields
            additionalFields = aboutSectionsData[1];
            for (var field in extendedProfileFields) {  // eslint-disable-line guard-for-in, no-restricted-syntax, vars-on-top, max-len
                fieldItem = extendedProfileFields[field];
                if (fieldItem.field_type === 'TextField') {
                    additionalFields.fields.push({
                        view: new AccountSettingsFieldViews.ExtendedFieldTextFieldView({
                            model: userAccountModel,
                            title: fieldItem.field_label,
                            fieldName: fieldItem.field_name,
                            valueAttribute: 'extended_profile',
                            persistChanges: persistChanges
                        })
                    });
                } else {
                    if (fieldItem.field_type === 'ListField') {
                        additionalFields.fields.push({
                            view: new AccountSettingsFieldViews.ExtendedFieldListFieldView({
                                model: userAccountModel,
                                title: fieldItem.field_label,
                                fieldName: fieldItem.field_name,
                                options: fieldItem.field_options,
                                valueAttribute: 'extended_profile',
                                persistChanges: persistChanges
                            })
                        });
                    }
                }
            }


            // Add the social link fields
            socialFields = {
                title: gettext('Social Media Links'),
                subtitle: gettext('Optionally, link your personal accounts to the social media icons on your edX profile.'),  // eslint-disable-line max-len
                fields: []
            };

            for (var socialPlatform in socialPlatforms) {  // eslint-disable-line guard-for-in, no-restricted-syntax, vars-on-top, max-len
                platformData = socialPlatforms[socialPlatform];
                socialFields.fields.push(
                    {
                        view: new AccountSettingsFieldViews.SocialLinkTextFieldView({
                            model: userAccountModel,
                            title: gettext(platformData.display_name + ' Link'),
                            valueAttribute: 'social_links',
                            helpMessage: gettext(
                                'Enter your ' + platformData.display_name + ' username or the URL to your ' +
                                platformData.display_name + ' page. Delete the URL to remove the link.'
                            ),
                            platform: socialPlatform,
                            persistChanges: persistChanges,
                            placeholder: platformData.example
                        })
                    }
                );
            }

            if (!isProgressForm) {
                aboutSectionsData.push(socialFields);

                // Add account deletion fields
                if (displayAccountDeletion) {
                    accountDeletionFields = {
                        title: gettext('Delete My Account'),
                        fields: [],
                        // Used so content can be rendered external to Backbone
                        domHookId: 'account-deletion-container'
                    };
                    aboutSectionsData.push(accountDeletionFields);
                }
            }


            // set TimeZoneField to listen to CountryField

            getUserField = function(list, search) {
                return _.find(list, function(field) {
                    return field.view.options.valueAttribute === search;
                }).view;
            };
            userFields = _.find(aboutSectionsData, function(section) {
                return section.title === gettext('Basic Account Information');
            }).fields;
            timeZoneDropdownField = getUserField(userFields, 'time_zone');
            countryDropdownField = getUserField(userFields, 'country');
            timeZoneDropdownField.listenToCountryView(countryDropdownField);

            var tabSections = {
                aboutTabSections: aboutSectionsData
            };

            if (authData.providers !== undefined && authData.providers.length !== 0) {
                accountsSectionData = [
                    {
                        title: gettext('Linked Accounts'),
                        subtitle: StringUtils.interpolate(
                            gettext('You can link your social media accounts to simplify signing in to {platform_name}.'),
                            {platform_name: platformName}
                        ),
                        fields: _.map(authData.providers, function(provider) {
                            return {
                                view: new AccountSettingsFieldViews.AuthFieldView({
                                    title: provider.name,
                                    valueAttribute: 'auth-' + provider.id,
                                    helpMessage: '',
                                    connected: provider.connected,
                                    connectUrl: provider.connect_url,
                                    acceptsLogins: provider.accepts_logins,
                                    disconnectUrl: provider.disconnect_url,
                                    platformName: platformName
                                })
                            };
                        })
                    }
                ];
                tabSections['accountsTabSections'] = accountsSectionData;
            }

            if (ordersHistoryData.length > 0) {
                ordersHistoryData.unshift(
                    {
                        title: gettext('ORDER NAME'),
                        order_date: gettext('ORDER PLACED'),
                        price: gettext('TOTAL'),
                        number: gettext('ORDER NUMBER')
                    }
                );

                ordersSectionData = [
                    {
                        title: gettext('My Orders'),
                        subtitle: StringUtils.interpolate(
                            gettext('This page contains information about orders that you have placed with {platform_name}.'),  // eslint-disable-line max-len
                            {platform_name: platformName}
                        ),
                        fields: _.map(ordersHistoryData, function(order) {
                            orderNumber = order.number;
                            if (orderNumber === 'ORDER NUMBER') {
                                orderNumber = 'orderId';
                            }
                            return {
                                view: new AccountSettingsFieldViews.OrderHistoryFieldView({
                                    totalPrice: order.price,
                                    orderId: order.number,
                                    orderDate: order.order_date,
                                    receiptUrl: order.receipt_url,
                                    valueAttribute: 'order-' + orderNumber,
                                    lines: order.lines
                                })
                            };
                        })
                    }
                ];
                tabSections['ordersTabSections'] = ordersSectionData;
            }

            accountSettingsView = new AccountSettingsView({
                model: userAccountModel,
                accountUserId: accountUserId,
                el: $accountSettingsElement,
                tabSections: tabSections,
                userPreferencesModel: userPreferencesModel,
                progress_form: isProgressForm
            });

            showAccountSettingsPage = function() {
                // Record that the account settings page was viewed.
                Logger.log('edx.user.settings.viewed', {
                    page: 'account',
                    visibility: null,
                    user_id: accountUserId
                });
            };

            showLoadingError = function() {
                accountSettingsView.showLoadingError();
            };

            userAccountModel.fetch({
                success: function() {
                    // Fetch the user preferences model
                    userPreferencesModel.fetch({
                        success: showAccountSettingsPage,
                        error: showLoadingError
                    });
                },
                error: showLoadingError
            });

            if (isProgressForm) {
                aboutSectionsData.map(function (el) {
                    var fields = el.fields;
                    var newFields = [];

                    fields.filter(function (field) {
                        if (listFormFields.indexOf(field.view.options.valueAttribute) !== -1) {
                            newFields.push(field);
                        }
                    });
                    el.fields = newFields;
                });
            }



            return {
                userAccountModel: userAccountModel,
                userPreferencesModel: userPreferencesModel,
                accountSettingsView: accountSettingsView
            };
        };
    });
}).call(this, define || RequireJS.define);
