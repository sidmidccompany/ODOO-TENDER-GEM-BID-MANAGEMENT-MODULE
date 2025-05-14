/* tender_widgets.js */
odoo.define('tender_management.widgets', function (require) {
"use strict";

var core = require('web.core');
var AbstractField = require('web.AbstractField');
var fieldRegistry = require('web.field_registry');
var field_utils = require('web.field_utils');
var QWeb = core.qweb;

/**
 * TenderAnalyticsChart widget
 * Displays analytics data in charts
 */
var TenderAnalyticsChart = AbstractField.extend({
    template: 'TenderAnalyticsChart',
    events: {},
    supportedFieldTypes: ['text'],
    
    /**
     * @override
     */
    init: function() {
        this._super.apply(this, arguments);
        this.charts = [];
    },
    
    /**
     * @override
     */
    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            self._renderCharts();
        });
    },
    
    /**
     * @override
     */
    destroy: function() {
        // Clean up chart instances
        _.each(this.charts, function(chart) {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = [];
        this._super.apply(this, arguments);
    },
    
    /**
     * @override
     */
    _render: function() {
        this._renderCharts();
    },
    
    /**
     * Render analytics charts
     *
     * @private
     */
    _renderCharts: function() {
        var self = this;
        // Clean up existing charts
        _.each(this.charts, function(chart) {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = [];
        
        // Parse the analytics data
        var analyticsData;
        try {
            analyticsData = JSON.parse(this.value || "{}");
        } catch (e) {
            console.error("Error parsing analytics data", e);
            this.$el.html('<div class="alert alert-danger">Invalid analytics data format</div>');
            return;
        }
        
        // Render the charts container
        this.$el.html(QWeb.render('TenderAnalyticsChartContent', {
            widget: this,
            data: analyticsData
        }));
        
        // Initialize Timeline Chart
        if (analyticsData.timeline && analyticsData.timeline.length) {
            var timelineData = this._prepareTimelineData(analyticsData.timeline);
            var timelineCtx = this.$('.o_tender_timeline_chart')[0].getContext('2d');
            
            var timelineChart = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: timelineData.labels,
                    datasets: [{
                        label: 'Timeline Events',
                        data: timelineData.data,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        pointRadius: 5,
                        pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                        pointHoverRadius: 7,
                        fill: false,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    title: {
                        display: true,
                        text: 'Tender Timeline'
                    },
                    scales: {
                        xAxes: [{
                            type: 'time',
                            time: {
                                unit: 'day',
                                displayFormats: {
                                    day: 'MMM D'
                                }
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Date'
                            }
                        }],
                        yAxes: [{
                            display: false
                        }]
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                return timelineData.events[tooltipItem.index];
                            }
                        }
                    }
                }
            });
            
            this.charts.push(timelineChart);
        }
        
        // Initialize Cost Breakdown Chart
        if (analyticsData.costs) {
            var costCtx = this.$('.o_tender_cost_chart')[0].getContext('2d');
            
            var costChart = new Chart(costCtx, {
                type: 'pie',
                data: {
                    labels: ['Preparation', 'Submission'],
                    datasets: [{
                        data: [
                            analyticsData.costs.preparation || 0,
                            analyticsData.costs.submission || 0,
                        ],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(54, 162, 235, 0.6)',
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    title: {
                        display: true,
                        text: 'Cost Breakdown'
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                var value = data.datasets[0].data[tooltipItem.index];
                                return data.labels[tooltipItem.index] + ': ' + field_utils.format.monetary(value);
                            }
                        }
                    }
                }
            });
            
            this.charts.push(costChart);
        }
        
        // Initialize Success Probability Gauge
        if ('win_probability' in analyticsData) {
            var gaugeCtx = this.$('.o_tender_probability_gauge')[0].getContext('2d');
            
            var gaugeChart = new Chart(gaugeCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Win Probability', 'Remaining'],
                    datasets: [{
                        data: [
                            analyticsData.win_probability || 0,
                            100 - (analyticsData.win_probability || 0)
                        ],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(200, 200, 200, 0.2)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    circumference: Math.PI,
                    rotation: -Math.PI,
                    cutoutPercentage: 80,
                    title: {
                        display: true,
                        text: 'Win Probability'
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                if (tooltipItem.index === 0) {
                                    return 'Win Probability: ' + data.datasets[0].data[0] + '%';
                                }
                                return '';
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            });
            
            this.charts.push(gaugeChart);
            
            // Add text in center
            var value = analyticsData.win_probability || 0;
            this.$('.o_gauge_value').html(value + '%');
        }
    },
    
    /**
     * Prepare timeline data for chart
     *
     * @private
     * @param {Array} timeline - Timeline events
     * @returns {Object} - Prepared data for chart
     */
    _prepareTimelineData: function(timeline) {
        var labels = [];
        var data = [];
        var events = [];
        
        _.each(timeline, function(event, index) {
            labels.push(event.date);
            data.push(index + 1); // Sequential positions for Y axis
            events.push(event.event);
        });
        
        return {
            labels: labels,
            data: data,
            events: events
        };
    }
});

/**
 * Dashboard Graph Widget
 * Displays data in various chart formats for the dashboard
 */
var TenderDashboardGraph = AbstractField.extend({
    className: 'o_tender_dashboard_graph',
    supportedFieldTypes: ['text'],
    
    /**
     * @override
     */
    init: function() {
        this._super.apply(this, arguments);
        this.chart = null;
    },
    
    /**
     * @override
     */
    destroy: function() {
        if (this.chart) {
            this.chart.destroy();
        }
        this._super.apply(this, arguments);
    },
    
    /**
     * @override
     */
    _render: function() {
        var self = this;
        
        // Parse the graph data
        var graphData;
        try {
            graphData = JSON.parse(this.value || "{}");
        } catch (e) {
            console.error("Error parsing graph data", e);
            this.$el.html('<div class="alert alert-danger">Invalid graph data format</div>');
            return;
        }
        
        if (_.isEmpty(graphData)) {
            this.$el.html('<div class="alert alert-info">No data available</div>');
            return;
        }
        
        // Clean up existing chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        // Create canvas
        this.$el.html('<canvas height="200"/>');
        var ctx = this.$('canvas')[0].getContext('2d');
        
        // Determine chart type
        var chartType = graphData.type || 'bar';
        
        // Create new chart
        this.chart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: graphData.labels || [],
                datasets: graphData.datasets || []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    display: true
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                }
            }
        });
    }
});

// Register custom widgets
fieldRegistry.add('tender_analytics_chart', TenderAnalyticsChart);
fieldRegistry.add('dashboard_graph', TenderDashboardGraph);

return {
    TenderAnalyticsChart: TenderAnalyticsChart,
    TenderDashboardGraph: TenderDashboardGraph
};

});
