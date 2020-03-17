import React from 'react';
import Slider from "react-slick";

import SingleWYSIWYGComponent from './SingleWYSIWYGComponent';
import Skaffolds from './Skaffolds';
import ActiveTable from './ActiveTable';


export default class Question extends React.Component{

    constructor(props) {
        super(props);

        this.changeQuestionType = this.changeQuestionType.bind(this);
        this.changeOptionCorrectness = this.changeOptionCorrectness.bind(this);
        this.changeOptionTitle = this.changeOptionTitle.bind(this);
        this.changeDescription = this.changeDescription.bind(this);
        this.scaffoldEditingStateChange = this.scaffoldEditingStateChange.bind(this);
        this.changeAnswer = this.changeAnswer.bind(this);
        this.getOptions = this.getOptions.bind(this);
        this.getButtonAddOption = this.getButtonAddOption.bind(this);
        this.changeTableData = this.changeTableData.bind(this);
        this.changeProblemTypeTitle = this.changeProblemTypeTitle.bind(this);
        this.disableScaffolds = this.disableScaffolds.bind(this);

        this.state = {
            showSimulation: false,
            scaffoldEditing: false
        };

        this.settingsImg = {
            arrows: true,
            dots: false,
            infinite: false,
            speed: 500,
            slidesToShow: 1,
            slidesToScroll: 1,
        };
    }

    changeQuestionType(e) {
        const dataset = e.target.dataset;
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    ...problemType,
                    type: dataset.type,
                    options: problemType.options.map(opt => {
                        return {
                            correct: false,
                            title: opt.title
                        };
                    }),
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    addOptionItem(e) {
        const problemTypeIndex = e.target.dataset.problemTypeIndex;
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];

        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +problemTypeIndex) {
                return {
                    ...problemType,
                    options: problemType.options.concat([{
                        correct: false,
                        title: ""
                    }])
                };
            }
            return problemType;
        });

        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    removeOptionItem(e) {
        const dataset = e.target.dataset;
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];

        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    type: problemType.type,
                    options: problemType.options.filter((el, ind) => ind !== +dataset.index)
                };
            }
            return problemType;
        });

        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    changeOptionCorrectness(e) {
        const dataset = e.target.dataset;
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    ...problemType,
                    options: problemType.options.map((opt, ind) => {
                        if (['select', 'radio'].includes(problemType.type)) {
                            if (ind === +dataset.index) {
                                return {
                                    correct: e.target.checked,
                                    title: opt.title
                                };
                            } else {
                                return {
                                    correct: false,
                                    title: opt.title
                                };
                            }
                        } else {
                            if (ind === +dataset.index) {
                                return {
                                    correct: e.target.checked,
                                    title: opt.title
                                };
                            } else {
                                return opt;
                            }
                        }
                    })
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    changeOptionTitle(e) {
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];
        const dataset = e.target.dataset;
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    ...problemType,
                    options: problemType.options.map((opt, _ind) => {
                        if (_ind === +dataset.index) {
                            return {
                                ...opt,
                                title: e.target.value
                            };
                        } else {
                            return opt;
                        }
                    })
                }
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    changeDescription(content) {
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            description: content
        });
    }

    addImage() {
        let activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            imgUrls: activeQuestion.imgUrls.concat([''])
        });
    }

    removeImage(e) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            imgUrls: activeQuestion.imgUrls.filter((el, ind) => {return ind !== +e.target.dataset.index})
        });
    }

    changeImage(e) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            imgUrls: activeQuestion.imgUrls.map((el, ind) => {
                if (ind === +e.target.dataset.index) {
                    return e.target.value;
                }
                return el;
            })
        });
    }

    changeIframeUrl(e) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            iframeUrl: e.target.value
        });
    }

    changeAnswer(e) {
        const dataset = e.target.dataset;
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    ...problemType,
                    answer: e.target.value
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    changePreciseness(e) {
        const dataset = e.target.dataset;
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === +dataset.problemTypeIndex) {
                return {
                    ...problemType,
                    preciseness: e.target.value
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    showSimulation() {
        this.setState({
            showSimulation: !this.state.showSimulation
        });
    }

    scaffoldEditingStateChange(value) {
        this.setState({
            scaffoldEditing: value
        });
    }

    scrollProblemTypes() {
        // smooth scroll to the last added problemType;
        const problemTypesHolder = document.getElementById('problem-types-holder');
        problemTypesHolder.style.height = problemTypesHolder.scrollHeight + 'px';
        problemTypesHolder.scrollTo({
            top: problemTypesHolder.scrollHeight,
            behavior: 'smooth'
        });
    }

    addProblemType() {
        this.props.questionAddNewProblemType(this.props.activeQuestionIndex);
        setTimeout(this.scrollProblemTypes, 100);
    }

    removeProblemType(e) {
        this.props.questionRemoveProblemType(+this.props.activeQuestionIndex, +e.target.dataset.problemTypeIndex);
        setTimeout(this.scrollProblemTypes, 100);
    }

    changeTableData(tableData, index) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === index) {
                return {
                    ...problemType,
                    tableData,
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    changeProblemTypeTitle(event, problemTypeIndex) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === problemTypeIndex) {
                return {
                    ...problemType,
                    title: event.target.value,
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    removeProblemTypeTitle(event, problemTypeIndex) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === problemTypeIndex) {
                const copyProblemType = {...problemType};
                delete copyProblemType['title'];
                return copyProblemType;
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }

    addProblemTypeTitle(event, problemTypeIndex) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        const problemTypes = activeQuestion.problemTypes.map((problemType, ind) => {
            if (ind === problemTypeIndex) {
                return {
                    ...problemType,
                    title: ''
                };
            }
            return problemType;
        });
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            problemTypes: problemTypes
        });
    }


    getOptions(problemType, index) {
        const type = problemType.type === 'select' ? 'radio' : problemType.type;
        const tableData = problemType.tableData || {};
        if (type === 'table') {
            return (
                <div className="questions__list number">
                    <ActiveTable tableData={tableData} problemTypeIndex={index} saveHandler={this.changeTableData}/>
                </div>
            );
        } else if (type === 'number') {
            return (
                <div className="questions__list number">
                    <div className="questions__list__item">
                        <input
                            className="questions__list__field"
                            type="number"
                            data-problem-type-index={index}
                            placeholder="Type numbers here"
                            value={problemType.answer}
                            onChange={this.changeAnswer.bind(this)}
                            />
                    </div>
                    <div className="questions__list__item">
                        <input
                            className="questions__list__field"
                            type="text"
                            data-problem-type-index={index}
                            value={problemType.preciseness}
                            onChange={this.changePreciseness.bind(this)}
                            placeholder="Add a tolerance"
                            />
                        <span className="questions__list__field-hint">It can be number or percentage like 12, 12.04 or 34%</span>
                    </div>
                </div>
            );
        } else if (type === 'text') {
            return (
                <div className="questions__list number">
                    <div className="questions__list__item">
                        <input
                            className="questions__list__field"
                            type="text"
                            data-problem-type-index={index}
                            placeholder="Enter Text"
                            value={problemType.answer}
                            onChange={this.changeAnswer.bind(this)}
                            />
                    </div>
                </div>
            );
        }
        return problemType.options.map((option, ind) => {
            return  (
                <div className="questions__list__item" key={ind+index}>
                    <label className="questions__list__label">
                        <input
                            key={ind+index}
                            data-index={ind}
                            data-problem-type-index={index}
                            onChange={this.changeOptionCorrectness}
                            className="questions__list__input"
                            type={type}
                            checked={option.correct}/>
                        <div className="questions__list__text">
                            <input
                                onChange={this.changeOptionTitle}
                                key={ind+index}
                                data-index={ind}
                                data-problem-type-index={index}
                                className="questions__list__text-hint"
                                type="text"
                                placeholder="Type answer text here..."
                                value={option.title}
                                />
                        </div>
                    </label>
                    {problemType.options.length > 1 && (
                        <button className="questions__list__remove-item" title="Remove item">
                            <i
                                className="fa fa-trash-o"
                                data-problem-type-index={index}
                                aria-hidden="true" data-index={ind} onClick={this.removeOptionItem.bind(this)} />
                        </button>
                    )}
                </div>
            );
        });
    };

    getButtonAddOption(type, index) {
        if (!['number', 'text', 'table'].includes(type)) {
            return (
                <div className="questions__list__add-item">
                    <button
                        type="button"
                        className="questions__list__add-item__btn"
                        data-problem-type-index={index}
                        onClick={this.addOptionItem.bind(this)}>
                        + add item
                    </button>
                </div>
            );
        }
    };

    disableScaffolds(e) {
        const activeQuestion = {...this.props.questions[this.props.activeQuestionIndex]};
        this.props.questionChanged(this.props.activeQuestionIndex, {
            ...activeQuestion,
            isScaffoldsEnabled: !activeQuestion.isScaffoldsEnabled
        });
    }

    render() {
        const activeQuestion = this.props.questions[this.props.activeQuestionIndex];
        if (!activeQuestion) {
            return null;
        }
        // this hack just to understand if we need to reset content for the TinyMCE editor in the SingleWYSIWYGComponent
        const shouldResetEditor = this.props.activeQuestionIndex !== this.activeQuestionIndex;

        this.activeQuestionIndex = this.props.activeQuestionIndex;

        return (
            <div className={`author-block__wrapper${this.state.scaffoldEditing ? ' is-scaffold-open' : ''}`}>
                <div className="author-block__content">
                    <div className="author-block__image">
                        {
                            this.state.showSimulation ? (
                                <iframe src={activeQuestion.iframeUrl} frameborder="0" />
                            ) : (
                                <div className="questions-images">
                                    {activeQuestion.imgUrls.map((imgUrl, ind) => {
                                        return (
                                            <img key={ind} src={imgUrl} alt=""/>
                                        )
                                    })}
                                </div>
                            )
                        }
                        {
                            activeQuestion.imgUrls.length === 0 && !this.state.showSimulation && (
                                <div className="author-block__image-selector">
                                    <i className="fa fa-picture-o" aria-hidden="true" />
                                    <br/>
                                    <button type="button" onClick={this.addImage.bind(this)} className="author-block__image-selector__btn">
                                        + Add image
                                    </button>
                                </div>
                            )
                        }
                    </div>
                    <div className="author-block__question" id="problem-types-holder">
                        <div className="text-editor__holder">
                            <SingleWYSIWYGComponent
                                class={`single-question-${this.activeQuestionIndex}`}
                                shouldReset={shouldResetEditor}
                                changeHandler={this.changeDescription}
                                content={activeQuestion.description}
                                />
                        </div>
                        {
                            activeQuestion.problemTypes.map((problemType, index) => {
                                return (
                                    <div className={`questions__wrapper is-${problemType.type}`} key={index}>
                                        <div className="questions-title">
                                            <div className="questions-title__input">
                                                {
                                                    problemType.title !== undefined ? (
                                                        <div>
                                                            <textarea
                                                                placeholder="Add the question text"
                                                                key={this.props.activeQuestionIndex + index}
                                                                value={problemType.title}
                                                                onChange={(event) => {this.changeProblemTypeTitle(event, index)}}/>
                                                            <button
                                                                type="button"
                                                                className="questions-title__btn-remove"
                                                                onClick={(event) => this.removeProblemTypeTitle(event, index)}>
                                                                <i className="fa fa-trash" aria-hidden="true" />
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <div className="questions-title__buttons">
                                                            <button type="button"
                                                                className="btn-add"
                                                                onClick={(event) => this.addProblemTypeTitle(event, index)}>
                                                                + add title
                                                            </button>
                                                        </div>
                                                    )
                                                }
                                            </div>
                                        </div>
                                        <div className="questions__list__toolbar">
                                            <button
                                                title='Radio'
                                                type="button"
                                                className={`questions__list__toolbar__btn ${problemType.type === 'radio' ? 'is-active' : ''}`}>
                                                <i
                                                    className="fa fa-dot-circle-o"
                                                    data-type="radio"
                                                    data-problem-type-index={index}
                                                    aria-hidden="true"
                                                    onClick={this.changeQuestionType}/>
                                            </button>
                                            <button
                                                title='Checkbox'
                                                type="button"
                                                className={`questions__list__toolbar__btn ${problemType.type === 'checkbox' ? 'is-active' : ''}`}>
                                                <i
                                                    className="fa fa-check-square-o"
                                                    data-type="checkbox"
                                                    data-problem-type-index={index}
                                                    aria-hidden="true"
                                                    onClick={this.changeQuestionType} />
                                            </button>
                                            <button
                                                title='Dropdown'
                                                type="button"
                                                className={`questions__list__toolbar__btn ${problemType.type === 'select' ? 'is-active' : ''}`}>
                                                <i
                                                    className="fa fa-list-alt"
                                                    data-type="select"
                                                    data-problem-type-index={index}
                                                    aria-hidden="true"
                                                    onClick={this.changeQuestionType} />
                                            </button>
                                            <button
                                                title='Numerical'
                                                type="button"
                                                data-type="number"
                                                data-problem-type-index={index}
                                                onClick={this.changeQuestionType}
                                                className={`questions__list__toolbar__btn ${problemType.type === 'number' ? 'is-active' : ''}`}>
                                                123...
                                            </button>
                                            <button
                                                title='Text'
                                                type="button"
                                                data-type="text"
                                                data-problem-type-index={index}
                                                onClick={this.changeQuestionType}
                                                className={`questions__list__toolbar__btn ${problemType.type === 'text' ? 'is-active' : ''}`}>
                                                Text
                                            </button>
                                            <button
                                                title="Table"
                                                type="button"
                                                className={`questions__list__toolbar__btn ${problemType.type === 'table' ? 'is-active' : ''}`}>
                                                <i
                                                    className="fa fa-table"
                                                    aria-hidden="true"
                                                    data-type="table"
                                                    data-problem-type-index={index}
                                                    onClick={this.changeQuestionType}
                                                    
                                                    ></i>
                                            </button>
                                        </div>

                                        <div className="questions__list">
                                            {this.getOptions(problemType, index)}
                                        </div>
                                        {this.getButtonAddOption(problemType.type, index)}
                                        <div className="questions-toolbar-add">
                                            {
                                                index === activeQuestion.problemTypes.length - 1 && (
                                                    <button className="questions-toolbar-add__btn is-add" type="button" onClick={this.addProblemType.bind(this)}>
                                                        <i className="fa fa-plus-square" aria-hidden="true" />
                                                    </button>
                                                )
                                            }
                                            {
                                                activeQuestion.problemTypes.length > 1 && (
                                                    <button className="questions-toolbar-add__btn is-remove" type="button" data-problem-type-index={index} onClick={this.removeProblemType.bind(this)}>
                                                        <i className="fa fa-trash" aria-hidden="true" />
                                                    </button>
                                                )
                                            }
                                        </div>
                                    </div>
                                )
                            })
                        }
                    </div>
                </div>
                <div className="questions-toolbar">
                    <div className="author-toolbar">
                        {
                            activeQuestion.iframeUrl && (
                                <div className="author-toolbar__row">
                                    <button className="author-toolbar__btn regular" onClick={this.showSimulation.bind(this)}>
                                        {this.state.showSimulation ? 'Show Images' : 'Show simulation'}
                                    </button>
                                </div>
                            )
                        }

                        <div className="author-toolbar__row">
                            {
                                activeQuestion.imgUrls.map((img, ind) => {
                                    return (
                                        <div className="author-toolbar__row-holder">
                                            <input
                                                className="author-toolbar__field"
                                                type="text"
                                                onChange={this.changeImage.bind(this)}
                                                value={img}
                                                key={ind}
                                                data-index={ind}
                                                placeholder='Paste URL of the image'
                                            />
                                            <button className="author-toolbar__btn cancel" data-index={ind} onClick={this.removeImage.bind(this)}>
                                                <i className="fa fa-trash-o" aria-hidden="true" />
                                            </button>
                                        </div>
                                    )})
                            }
                            {
                                activeQuestion.imgUrls.length > 0 && (
                                    <div className="author-toolbar__add">
                                        <button className="author-toolbar__add__btn" onClick={this.addImage.bind(this)}>
                                            + add image
                                        </button>
                                    </div>
                                )
                            }
                        </div>
                        <div className="author-toolbar__row">
                            <p>"Show simulation" iframe url</p>
                            <input
                                className="author-toolbar__field is-full"
                                type="text"
                                onChange={this.changeIframeUrl.bind(this)}
                                value={activeQuestion.iframeUrl}
                                placeholder='Paste URL of the iframe'
                            />
                        </div>
                    </div>
                    <div className="scaffolds-holder">
                        <div className="scaffolds-switch">
                            <span className="scaffolds-switch_text">Enable/Disable Scaffolds</span>
                            <label className="scaffolds-switch_label">
                                <input
                                    type="checkbox"
                                    onChange={this.disableScaffolds}
                                    checked={activeQuestion.isScaffoldsEnabled}
                                />
                                <span className="scaffolds-switch_slider is-round"/>
                            </label>
                        </div>
                        { activeQuestion.isScaffoldsEnabled && (
                            <Skaffolds
                                questionChanged={this.props.questionChanged}
                                activeQuestion={activeQuestion}
                                activeQuestionIndex={this.props.activeQuestionIndex}
                                scaffoldEditingStateChange={this.scaffoldEditingStateChange}
                            />
                        )}
                    </div>
                </div>

                <div className="author-block__buttons">
                    <button type="button" className="author-block__btn">
                        Next
                    </button>
                </div>
            </div>
        )
    }
}
