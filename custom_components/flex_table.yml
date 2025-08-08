type: custom:flex-table-card
title: Wine Cellar Dashboard
entities:
  include:
    - sensor.cellar_tracker_wine*
clickable: true
tap_action:
  action: more-info
unsafe_render_html: true
columns:
  - name: Wine
    data: state
    click_action: more-info
  - name: Rack
    data: location
  - name: Bin
    data: bins
    modify: |
      (() => {
        if (!x || x.length === 0) return '';
        return Array.isArray(x) ? x.join(', ') : x;
      })()
  - name: Country
    data: country
  - name: BeginConsume
    data: beginconsume
    modify: |
      (() => {
        const year = new Date().getFullYear();
        const val = parseInt(x);
        const color = val > year ? 'red' : 'green';
        return `<span style="color:${color}">${x}</span>`;
      })()
  - name: EndConsume
    data: endconsume
    modify: |
      (() => {
        const year = new Date().getFullYear();
        const val = parseInt(x);
        const color = val > year ? 'green' : 'red';
        return `<span style="color:${color}">${x}</span>`;
      })()
  - name: Value
    data: value_avg
    type: numeric
    suffix: " kr"
    modify: parseFloat(x).toFixed(0)
