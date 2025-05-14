/* tender_ai_chat.js */
odoo.define('tender_management.ai_chat', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var rpc = require('web.rpc');
var session = require('web.session');
var QWeb = core.qweb;

var TenderAIChat = Widget.extend({
    template: 'TenderAIChat',
    events: {
        'click .o_tender_ai_send': '_onSendMessage',
        'keydown .o_tender_ai_input': '_onInputKeydown',
        'click .o_ai_suggestion': '_onSuggestionClick',
        'click .o_ai_clear_chat': '_onClearChat',
        'click .o_ai_toggle_suggestions': '_onToggleSuggestions',
    },

    /**
     * @override
     */
    init: function(parent, options) {
        this._super.apply(this, arguments);
        this.options = options || {};
        this.tenderId = this.options.tenderId;
        this.messages = [];
        this.suggestions = [
            "What are the key requirements for this tender?",
            "Generate a compliance checklist for this tender",
            "What are the main evaluation criteria?",
            "Suggest a competitive pricing strategy",
            "Analyze the tender's risks and opportunities",
            "Draft a technical response for section 3.2",
            "What similar tenders have we won in the past?",
            "Generate a bid summary report"
        ];
        this.showSuggestions = true;
        this.isProcessing = false;
    },

    /**
     * @override
     */
    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            self._renderChat();
            self._focusInput();
            // Initial greeting from AI assistant
            self._addSystemMessage("Hello! I'm your Tender Assistant. I can help with analyzing tender requirements, creating compliance checklists, drafting responses, and suggesting strategies. How can I help you today?");
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Render the chat interface
     *
     * @private
     */
    _renderChat: function() {
        this.$('.o_tender_ai_chat_content').html(QWeb.render('TenderAIChatMessages', {
            messages: this.messages,
            suggestions: this.suggestions,
            showSuggestions: this.showSuggestions
        }));
        this._scrollToBottom();
    },

    /**
     * Add a user message to the chat
     *
     * @private
     * @param {String} content - The message content
     */
    _addUserMessage: function(content) {
        if (!content.trim()) {
            return;
        }
        
        this.messages.push({
            type: 'user',
            content: content,
            datetime: moment().format('HH:mm')
        });
        
        this._renderChat();
        this._scrollToBottom();
    },

    /**
     * Add a system message to the chat
     *
     * @private
     * @param {String} content - The message content
     */
    _addSystemMessage: function(content) {
        this.messages.push({
            type: 'system',
            content: content,
            datetime: moment().format('HH:mm')
        });
        
        this._renderChat();
        this._scrollToBottom();
    },

    /**
     * Add a processing message to the chat
     *
     * @private
     */
    _addProcessingMessage: function() {
        this.isProcessing = true;
        this.messages.push({
            type: 'system',
            isProcessing: true,
            content: 'Thinking...',
            datetime: moment().format('HH:mm')
        });
        
        this._renderChat();
        this._scrollToBottom();
    },

    /**
     * Update the last processing message with actual content
     *
     * @private
     * @param {String} content - The message content
     */
    _updateProcessingMessage: function(content) {
        var lastMessage = this.messages[this.messages.length - 1];
        if (lastMessage && lastMessage.isProcessing) {
            lastMessage.isProcessing = false;
            lastMessage.content = content;
            this.isProcessing = false;
            
            this._renderChat();
            this._scrollToBottom();
        }
    },

    /**
     * Send a message to the AI assistant
     *
     * @private
     * @param {String} message - The message to send
     */
    _sendMessage: function(message) {
        var self = this;
        
        // Don't send empty messages or when processing
        if (!message.trim() || this.isProcessing) {
            return;
        }
        
        // Add user message to chat
        this._addUserMessage(message);
        
        // Clear input
        this.$('.o_tender_ai_input').val('');
        
        // Show processing indicator
        this._addProcessingMessage();
        
        // Call the backend to get AI response
        rpc.query({
            model: 'tender.tender',
            method: 'get_ai_assistant_response',
            args: [this.tenderId, message]
        }).then(function(result) {
            // Update processing message with actual response
            self._updateProcessingMessage(result.response);
        }).guardedCatch(function(error) {
            // Handle error
            self._updateProcessingMessage("I'm sorry, I couldn't process your request. Please try again later.");
        });
    },

    /**
     * Scroll chat to the bottom
     *
     * @private
     */
    _scrollToBottom: function() {
        var $chatContent = this.$('.o_tender_ai_chat_content');
        $chatContent.scrollTop($chatContent.prop('scrollHeight'));
    },

    /**
     * Focus on the input field
     *
     * @private
     */
    _focusInput: function() {
        this.$('.o_tender_ai_input').focus();
    },

    /**
     * Clear the chat
     *
     * @private
     */
    _clearChat: function() {
        // Keep only the first (greeting) message
        if (this.messages.length > 0) {
            var greeting = this.messages[0];
            this.messages = [greeting];
            this._renderChat();
        }
    },

    /**
     * Toggle suggestions visibility
     *
     * @private
     */
    _toggleSuggestions: function() {
        this.showSuggestions = !this.showSuggestions;
        this._renderChat();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handle sending message button click
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onSendMessage: function(ev) {
        var message = this.$('.o_tender_ai_input').val();
        this._sendMessage(message);
    },

    /**
     * Handle keydown in input field (Enter to send)
     *
     * @private
     * @param {KeyboardEvent} ev
     */
    _onInputKeydown: function(ev) {
        if (ev.which === 13 && !ev.shiftKey) { // Enter without shift
            ev.preventDefault();
            var message = this.$('.o_tender_ai_input').val();
            this._sendMessage(message);
        }
    },

    /**
     * Handle click on a suggestion
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onSuggestionClick: function(ev) {
        var suggestion = $(ev.currentTarget).text();
        this._sendMessage(suggestion);
    },

    /**
     * Handle clear chat button click
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onClearChat: function(ev) {
        this._clearChat();
    },

    /**
     * Handle toggle suggestions button click
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onToggleSuggestions: function(ev) {
        this._toggleSuggestions();
    }
});

return TenderAIChat;

});
