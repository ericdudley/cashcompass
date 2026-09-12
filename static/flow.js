(() => {
  const colorForKind = (kind) => {
    const styles = getComputedStyle(document.documentElement);
    const themeColor = (name, fallback) => styles.getPropertyValue(name).trim() || fallback;
    const colors = {
      income: themeColor('--color-success', '#34d399'),
      after_tax: themeColor('--color-primary', '#60a5fa'),
      pool: themeColor('--color-secondary', '#a78bfa'),
      tax: themeColor('--color-error', '#f87171'),
      expense: themeColor('--color-error', '#fb7185'),
      leftover: themeColor('--color-success', '#34d399'),
      shortfall: themeColor('--color-warning', '#fbbf24'),
      refund: themeColor('--color-info', '#38bdf8'),
    };
    return colors[kind] || themeColor('--color-neutral', '#94a3b8');
  };

  const initFlowChart = (root) => {
    if (!root || root.dataset.flowReady === 'true') return;
    root.dataset.flowReady = 'true';

    let graphData;
    try {
      graphData = JSON.parse(root.dataset.flowGraph || '{}');
    } catch (_error) {
      root.textContent = 'The flow diagram data could not be read.';
      return;
    }

    if (!window.d3 || typeof window.d3.sankey !== 'function') {
      root.textContent = 'The interactive diagram could not load. Exact values are available below.';
      root.dataset.flowChartError = 'library-unavailable';
      return;
    }

    const tooltip = document.getElementById('flow-tooltip');
    let resizeFrame = 0;
    let renderedWidth = 0;

    const hideTooltip = () => {
      if (!tooltip) return;
      tooltip.classList.add('hidden');
      tooltip.replaceChildren();
    };

    const showTooltip = (datum, anchor) => {
      if (!tooltip) return;
      const title = document.createElement('p');
      title.className = 'font-medium text-base-content';
      title.textContent = datum.label || `${datum.source.label} → ${datum.target.label}`;

      const value = document.createElement('p');
      value.className = 'font-mono text-sm text-base-content';
      value.textContent = datum.value_fmt || datum.valueFmt || '';

      tooltip.replaceChildren(title, value);
      if (datum.percentage) {
        const percentage = document.createElement('p');
        percentage.className = 'text-xs cc-muted';
        percentage.textContent = `${datum.percentage} ${datum.percentage_label || ''}`.trim();
        tooltip.append(percentage);
      }
      tooltip.classList.remove('hidden');

      const rect = anchor.getBoundingClientRect();
      const tipRect = tooltip.getBoundingClientRect();
      const left = Math.min(
        window.innerWidth - tipRect.width - 8,
        Math.max(8, rect.left + rect.width / 2 - tipRect.width / 2),
      );
      let top = rect.top - tipRect.height - 8;
      if (top < 8) top = Math.min(window.innerHeight - tipRect.height - 8, rect.bottom + 8);
      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${Math.max(8, top)}px`;
    };

    const render = () => {
      hideTooltip();
      root.replaceChildren();

      const width = Math.max(root.clientWidth, 760);
      renderedWidth = width;
      const nodeCount = (graphData.nodes || []).length;
      const height = Math.max(500, Math.min(900, nodeCount * 48));
      const margin = { top: 42, right: 170, bottom: 24, left: 150 };
      const graph = {
        nodes: (graphData.nodes || []).map((node) => ({ ...node })),
        links: (graphData.links || []).map((link) => ({ ...link })),
      };

      if (!graph.links.length) {
        root.textContent = 'There is not enough non-zero data to draw a flow diagram.';
        return;
      }

      const sankey = window.d3.sankey()
        .nodeId((node) => node.id)
        .nodeWidth(18)
        .nodePadding(28)
        .nodeAlign(window.d3.sankeyJustify)
        .nodeSort((a, b) => {
          const orderA = Number.isFinite(a.sort_order) ? a.sort_order : 0;
          const orderB = Number.isFinite(b.sort_order) ? b.sort_order : 0;
          return orderA - orderB || a.id.localeCompare(b.id);
        })
        .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]]);
      sankey(graph);

      const svg = window.d3.select(root)
        .append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('width', width)
        .attr('height', height)
        .attr('role', 'group')
        .attr('aria-label', `Sankey diagram for ${graphData.year}`)
        .attr('data-testid', 'flow-sankey');

      const linkSelection = svg.append('g')
        .attr('fill', 'none')
        .selectAll('path')
        .data(graph.links)
        .join('path')
        .attr('d', window.d3.sankeyLinkHorizontal())
        .attr('stroke', (link) => colorForKind(link.target.kind))
        .attr('stroke-width', (link) => Math.max(1, link.width))
        .attr('stroke-opacity', 0.34)
        .attr('tabindex', 0)
        .attr('data-flow-link', (link) => `${link.source.id}:${link.target.id}`)
        .attr('aria-label', (link) => `${link.source.label} to ${link.target.label}: ${link.value_fmt}`)
        .style('outline', 'none');

      const nodeSelection = svg.append('g')
        .selectAll('g')
        .data(graph.nodes)
        .join('g')
        .attr('tabindex', 0)
        .attr('role', (node) => node.url ? 'link' : 'img')
        .attr('aria-label', (node) => `${node.label}: ${node.value_fmt}`)
        .attr('data-flow-node-id', (node) => node.id)
        .attr('data-flow-node-kind', (node) => node.kind)
        .style('cursor', (node) => node.url ? 'pointer' : 'default')
        .style('outline', 'none');

      const maxLayer = Math.max(...graph.nodes.map((node) => node.layer));
      const labelX = (node) => {
        if (node.layer === 0) return node.x1 + 8;
        if (node.layer === maxLayer) return node.x0 - 8;
        return (node.x0 + node.x1) / 2;
      };
      const labelY = (node) => node.layer > 0 && node.layer < maxLayer
        ? Math.max(16, node.y0 - 18)
        : (node.y0 + node.y1) / 2;
      const labelAnchor = (node) => {
        if (node.layer === 0) return 'start';
        if (node.layer === maxLayer) return 'end';
        return 'middle';
      };

      const groupedNodes = new Map();
      graph.nodes.forEach((node) => {
        if (!node.group || !node.group_label) return;
        const current = groupedNodes.get(node.group);
        if (!current || node.y0 < current.y0) groupedNodes.set(node.group, node);
      });
      const groupHeadings = [...groupedNodes.values()].sort((a, b) => a.y0 - b.y0);
      svg.append('g')
        .attr('aria-label', 'Flow groups')
        .selectAll('text')
        .data(groupHeadings)
        .join('text')
        .attr('x', labelX)
        .attr('y', (node) => Math.max(16, node.y0 - 10))
        .attr('text-anchor', labelAnchor)
        .attr('class', 'cc-flow-group-label')
        .attr('data-flow-group-id', (node) => node.group)
        .attr('role', 'heading')
        .attr('aria-level', '3')
        .text((node) => node.group_label);

      nodeSelection.append('rect')
        .attr('x', (node) => node.x0)
        .attr('y', (node) => node.y0)
        .attr('height', (node) => Math.max(1, node.y1 - node.y0))
        .attr('width', (node) => node.x1 - node.x0)
        .attr('rx', 3)
        .attr('fill', (node) => colorForKind(node.kind));

      nodeSelection.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('dy', '-0.15em')
        .attr('text-anchor', labelAnchor)
        .attr('class', 'cc-flow-label')
        .text((node) => node.label);

      nodeSelection.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('dy', '1.15em')
        .attr('text-anchor', labelAnchor)
        .attr('class', 'cc-flow-value')
        .text((node) => node.value_fmt);

      const ancestors = (node) => {
        const ids = new Set([node.id]);
        const queue = [node];
        while (queue.length) {
          const current = queue.shift();
          current.targetLinks.forEach((link) => {
            if (!ids.has(link.source.id)) {
              ids.add(link.source.id);
              queue.push(link.source);
            }
          });
        }
        return ids;
      };

      const descendants = (node) => {
        const ids = new Set([node.id]);
        const queue = [node];
        while (queue.length) {
          const current = queue.shift();
          current.sourceLinks.forEach((link) => {
            if (!ids.has(link.target.id)) {
              ids.add(link.target.id);
              queue.push(link.target);
            }
          });
        }
        return ids;
      };

      const highlightNode = (node) => {
        const ids = new Set([...ancestors(node), ...descendants(node)]);
        nodeSelection.classed('cc-flow-dimmed', (candidate) => !ids.has(candidate.id));
        linkSelection
          .classed('cc-flow-dimmed', (link) => !ids.has(link.source.id) || !ids.has(link.target.id))
          .attr('stroke-opacity', (link) => ids.has(link.source.id) && ids.has(link.target.id) ? 0.68 : 0.08);
      };

      const highlightLink = (link) => {
        nodeSelection.classed('cc-flow-dimmed', (node) => node.id !== link.source.id && node.id !== link.target.id);
        linkSelection
          .classed('cc-flow-dimmed', (candidate) => candidate !== link)
          .attr('stroke-opacity', (candidate) => candidate === link ? 0.76 : 0.08);
      };

      const clearHighlight = () => {
        nodeSelection.classed('cc-flow-dimmed', false);
        linkSelection.classed('cc-flow-dimmed', false).attr('stroke-opacity', 0.34);
        hideTooltip();
      };

      nodeSelection
        .on('mouseenter focus', function (_event, node) {
          highlightNode(node);
          showTooltip(node, this);
        })
        .on('mouseleave', function () {
          if (document.activeElement !== this) clearHighlight();
        })
        .on('blur', clearHighlight)
        .on('click', (_event, node) => {
          if (node.url) window.location.assign(node.url);
        })
        .on('keydown', (event, node) => {
          if (node.url && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            window.location.assign(node.url);
          }
        });

      linkSelection
        .on('mouseenter focus', function (_event, link) {
          highlightLink(link);
          showTooltip(link, this);
        })
        .on('mouseleave', function () {
          if (document.activeElement !== this) clearHighlight();
        })
        .on('blur', clearHighlight);
    };

    render();
    const observer = new ResizeObserver(() => {
      const nextWidth = Math.max(root.clientWidth, 760);
      if (Math.abs(nextWidth - renderedWidth) < 1) return;
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(render);
    });
    observer.observe(root);
  };

  const initAll = () => document.querySelectorAll('[data-flow-graph]').forEach(initFlowChart);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
  document.addEventListener('htmx:afterSwap', initAll);
})();
