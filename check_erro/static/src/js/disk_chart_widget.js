/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class DiskChartWidget extends Component {
    static template = 'check_erro.DiskChartTemplate';
    static props = {
        ...standardFieldProps
    };

    setup() {
        this.orm = this.env.services.orm;
        this.renderChart();
    }

    async renderChart() {
        try {
            const result = await this.orm.call(
                'telegraf.disk',
                'get_disk_usage_data',
                [this.props.record.data.device, this.props.record.data.days || 1]
            );

            // Đợi cho đến khi component được mount
            await new Promise(resolve => setTimeout(resolve, 0));
            const canvas = this.el.querySelector('canvas');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: result,
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'hour',
                                displayFormats: {
                                    hour: 'HH:mm'
                                }
                            },
                            title: {
                                display: true,
                                text: 'Thời gian'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Dung lượng đã sử dụng (GB)'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering chart:', error);
        }
    }
}

export const diskChartField = {
    component: DiskChartWidget,
    supportedTypes: ['text'],
};

registry.category("fields").add("chart", diskChartField); 