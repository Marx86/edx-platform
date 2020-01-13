import React from 'react';

import WYSWYGComponent from './WYSWYGComponent';

export default class SingleWYSIWYGComponent extends WYSWYGComponent{

    changeHandler(e) {
        this.props.changeHandler(e.target.getContent());
    }

    getClassName() {
        return 'simple-hera-tinymce';
    }
}
