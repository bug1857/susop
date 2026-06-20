# SustainOCPM Reusable Component Library

This document specifies the conceptual metadata, structural properties, interfaces, interactive behaviors, accessibility attributes, and state mappings for the 27 core components of the SustainOCPM platform. All layout, font sizes, colors, and shadows map directly to the design tokens defined in [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md).

---

## 1. Navigation Components

### 1.1 Navigation Bar
* **Properties**: Logo container, global search placeholder, workspace switcher dropdown, profile/theme controller.
* **Inputs/Outputs**:
  * *Input*: `userProfile: Object`, `activeWorkspace: WorkspaceInfo`, `theme: 'light' | 'dark'`.
  * *Output*: `onWorkspaceChange(id: String)`, `onSearchTrigger(query: String)`, `onThemeToggle()`.
* **Interactive Behaviors**: Workspace dropdown expands on click with micro-active scaling; search input displays a modal backdrop focus shadow on active keyboard focus (Ctrl+K).
* **Accessibility**: `role="navigation"`, `aria-label="Global Navigation"`, `aria-haspopup="listbox"`, logical tab order.
* **State Mappings**: Highlights active workspace selected from the local configuration; displays persistent theme preference.

### 1.2 Sidebar
* **Properties**: Collapsible sidebar menu container, application module navigation links, status indicators.
* **Inputs/Outputs**:
  * *Input*: `currentPath: String`, `isCollapsed: Boolean`, `unresolvedAlertsCount: Integer`.
  * *Output*: `onToggleCollapse()`, `onNavigate(path: String)`.
* **Interactive Behaviors**: Sliding menu drawer animation; hover-state overlays a secondary blue accent.
* **Accessibility**: `aria-expanded`, dynamic text labels for screen readers when collapsed, `role="menubar"`.
* **State Mappings**: Linked to browser navigation state. Highlight active module page. Persistence of collapse state in session storage.

### 1.3 Breadcrumbs
* **Properties**: Horizontal path indicators separated by arrow delimiters, active leaf node label.
* **Inputs/Outputs**:
  * *Input*: `navigationSegments: List<{ label: String, url: String }>`
  * *Output*: `onSegmentClick(url: String)`.
* **Interactive Behaviors**: Segment link text underlines on hover.
* **Accessibility**: `role="navigation"`, `aria-label="Breadcrumbs"`, active segment marked with `aria-current="page"`.
* **State Mappings**: Inbound router history defines segment values dynamically.

---

## 2. Card & Visualization Containers

### 2.1 Metric Card
* **Properties**: Label text, numeric display value, comparative variance trend indicators, small sparkline visualization.
* **Inputs/Outputs**:
  * *Input*: `metricLabel: String`, `currentValue: Number`, `previousValue: Number`, `sparklineData: List<Point>`.
  * *Output*: `onMetricCardClick()`.
* **Interactive Behaviors**: Card scale-hover effect; sparkline highlights local coordinates on hover.
* **Accessibility**: `role="region"`, `aria-live="polite"`, descriptive screen-reader tags detailing absolute value and percentage shift.
* **State Mappings**: Auto-updates upon active filtering parameters; displays spinner during log calculations.

### 2.2 Insight Card
* **Properties**: Text description, severity badge, recommendation summary, detail toggle button.
* **Inputs/Outputs**:
  * *Input*: `insightData: { severity: String, description: String, actionTitle: String }`.
  * *Output*: `onApplyRecommendation()`.
* **Interactive Behaviors**: Detail panel expands inline with ease-in easing; focus outline applies on tab selection.
* **Accessibility**: `aria-expanded` toggle state, custom screen reader warnings for critical-priority insights.
* **State Mappings**: Subscribes to the AI multi-agent recommendation engine; maintains dismissed status in session state.

### 2.3 Chart Container
* **Properties**: Title bar, filter selections, main canvas viewport, hover legend tooltip.
* **Inputs/Outputs**:
  * *Input*: `chartTitle: String`, `chartData: SeriesObject`, `loadingState: Boolean`.
  * *Output*: `onFilterSelection(filterParams: Object)`.
* **Interactive Behaviors**: Zoom/drag selection box; hover state triggers data-point tooltip rendering with coordinates.
* **Accessibility**: Accessible backing tabular data fallback switch (`role="button"`), screen-reader labels for chart coordinates.
* **State Mappings**: Stores zoom scale levels in active workspace session storage to maintain coordinates across page navigations.

---

## 3. Advanced Process Elements

### 3.1 Process Graph
* **Properties**: OCPM network viewer, multi-object rendering nodes (JSON/XML logs), interactive nodes/edges, zoom controller.
* **Inputs/Outputs**:
  * *Input*: `ocelGraphData: { nodes: List<Node>, edges: List<Edge> }`, `selectedPath: String`.
  * *Output*: `onNodeClick(nodeId: String)`, `onEdgeHover(edgeId: String)`.
* **Interactive Behaviors**: Dynamic pan, drag-to-move, pinch-to-zoom; clicking a node pops open an explainability overlay; edge thickness varies on volume.
* **Accessibility**: Alternative tabular overview accessible via keyboard toggling; nodes focusable with aria-descriptions.
* **State Mappings**: Active path highlighting is synchronized with conformance indicators and cached in session storage.

### 3.2 Data Table
* **Properties**: Sortable column headers, cell grid, paginated footer navigation, inline status indicators.
* **Inputs/Outputs**:
  * *Input*: `columns: List<Column>`, `dataRows: List<Row>`, `pageSize: Integer`.
  * *Output*: `onSortChange(columnId: String)`, `onPageChange(pageNumber: Integer)`.
* **Interactive Behaviors**: Column header indicators rotate on active sort toggle; rows highlight on cursor hover.
* **Accessibility**: `role="grid"`, table header columns labeled with `aria-sort` attributes; page toggle keys reachable via Tab key.
* **State Mappings**: Sort/filter properties and page markers are persisted to prevent resets during browser refreshes.

---

## 4. Setup & Mapping Wizards

### 4.1 Upload Wizard
* **Properties**: Upload target boundary, drag-over file status indicators, format verification list.
* **Inputs/Outputs**:
  * *Input*: `allowedFormats: List<String>`, `maxFileSize: Bytes`.
  * *Output*: `onFileAccept(file: Blob)`, `onUploadProgress(percent: Number)`.
* **Interactive Behaviors**: Boundary border color shifts to interactive blue on drag enter; progress meter displays real-time parse bar.
* **Accessibility**: Live region screen announcements (`aria-live="assertive"`) detailing uploading completion rates or validation errors.
* **State Mappings**: Temporarily holds file buffer streams in session memory prior to schema verification steps.

### 4.2 Schema Mapping Wizard
* **Properties**: Source column field cards, target log schema parameters, validation status icons, drag connection threads.
* **Inputs/Outputs**:
  * *Input*: `detectedHeaders: List<String>`, `requiredFields: List<String>`.
  * *Output*: `onSchemaSubmit(mappings: Object)`.
* **Interactive Behaviors**: Drag connection lines between source headers and targets; error indicators toggle red upon mismatching data types.
* **Accessibility**: Dropdown option selector fallback for drag actions; keyboard drag-drop shortcuts provided via spacebar/arrows.
* **State Mappings**: Mappings are persisted to workspace storage templates to auto-apply schemas on next ingestion.

---

## 5. Decision & Panel Components

### 5.1 Recommendation Panel
* **Properties**: Header area, list of mitigation actions, projected benefits checklist (e.g., Lead time -15%, Carbon -2.4t).
* **Inputs/Outputs**:
  * *Input*: `recommendations: List<Recommendation>`, `activeContext: Object`.
  * *Output*: `onActionSelected(actionId: String)`.
* **Interactive Behaviors**: Action card collapses upon click selection; detailed calculations toggle open.
* **Accessibility**: Accordion headers wrapped in `<h3>` tags with `aria-controls` referencing matching details drawer.
* **State Mappings**: Syncs with AI Copilot outcomes to dynamically recommend steps based on the process path.

### 5.2 Alert Panel
* **Properties**: Alert category header, warning description, timestamp, dismissal button.
* **Inputs/Outputs**:
  * *Input*: `activeAlerts: List<Alert>`.
  * *Output*: `onDismissAlert(alertId: String)`.
* **Interactive Behaviors**: Alert slides out from viewport on dismissal; transition animation fades container border.
* **Accessibility**: `role="alert"`, screen reader focus forced to critical alerts upon initial rendering.
* **State Mappings**: Dismissed warnings list persisted across browser session records.

### 5.3 Report Viewer
* **Properties**: Page layout canvas, pagination controllers, print configuration options, zoom level slider.
* **Inputs/Outputs**:
  * *Input*: `reportTemplate: DocumentTemplate`, `reportData: Object`.
  * *Output*: `onExportDocument(format: String)`.
* **Interactive Behaviors**: Document segments scroll within container; hover indicators highlight editable text areas.
* **Accessibility**: Full tab navigation through report form pages, dynamic alt text updates on structural graphics.
* **State Mappings**: Remembers last navigated page index and selected report layout options on state reload.

---

## 6. Advanced Analytics Components

### 6.1 Benchmark Card
* **Properties**: Double-metric comparative comparison panels, average deviation graphs, target indicator overlays.
* **Inputs/Outputs**:
  * *Input*: `sourceMetrics: MetricGroup`, `targetMetrics: MetricGroup`.
  * *Output*: `onDetailsClick()`.
* **Interactive Behaviors**: Selecting either metric shifts comparison chart focus; details open in an overlay modal.
* **Accessibility**: Visual contrast compliance on overlay elements (minimum contrast ratio of 4.5:1).
* **State Mappings**: Compares current workspace analytics with selected external benchmark databases.

### 6.2 Digital Twin Viewer
* **Properties**: Process simulation diagram, throughput density indicators, bottleneck heat overlays.
* **Inputs/Outputs**:
  * *Input*: `processTwinData: Object`, `simulationSpeed: Double`.
  * *Output*: `onSimulationState(state: 'play' | 'pause' | 'stop')`.
* **Interactive Behaviors**: Node pulsing rates map process flows; speed sliders slide smoothly with micro-tick feedback.
* **Accessibility**: Text description overlays detailing average queue lengths per simulation step.
* **State Mappings**: Tracks execution status during run cycles; state configuration parameters are saved.

### 6.3 Scenario Simulator
* **Properties**: Parametric sliders (Resource Count, Demand Rate, Transit Speed), simulation run trigger button.
* **Inputs/Outputs**:
  * *Input*: `baselinePerformance: Object`, `bounds: RangeLimits`.
  * *Output*: `onSimulationComplete(outputMetrics: Object)`.
* **Interactive Behaviors**: Sliders update numerical tooltips dynamically; comparison bar charts slide up upon simulation output.
* **Accessibility**: Keyboard focus rings on sliders; manual input field fallback for slider parameters.
* **State Mappings**: Parameter presets persist in the workspace database to allow scenario re-evaluation.

---

## 7. AI Copilot Components

### 7.1 Knowledge Base Viewer
* **Properties**: Category table of contents, document rendering panel, markdown view, search input field.
* **Inputs/Outputs**:
  * *Input*: `indexStructure: List<Chapter>`, `selectedArticle: Article`.
  * *Output*: `onArticleSelect(articleId: String)`.
* **Interactive Behaviors**: Category items expand to sub-lists on click; selected items map background highlight.
* **Accessibility**: ARIA tree navigation structure (`role="tree"`, `role="treeitem"`, `aria-selected`).
* **State Mappings**: Maintains article navigation scroll coordinates on page refreshes.

### 7.2 AI Chat
* **Properties**: Chat log area, scroll position locker, system role message bubbles, text input block, token attachment bar.
* **Inputs/Outputs**:
  * *Input*: `messageHistory: List<Message>`, `isGenerating: Boolean`.
  * *Output*: `onSendMessage(text: String)`, `onAttachContext(item: ContextObject)`.
* **Interactive Behaviors**: Automated scrolling to baseline on new message; input expansion based on input content length.
* **Accessibility**: `role="log"`, screen reader announcements on response complete, input aria-labels.
* **State Mappings**: Session history is stored to prevent conversation resets during page navigation.

### 7.3 Prompt Suggestions
* **Properties**: Interactive prompt template cards, categorization tags.
* **Inputs/Outputs**:
  * *Input*: `templates: List<PromptTemplate>`.
  * *Output*: `onSuggestionClick(promptText: String)`.
* **Interactive Behaviors**: Click action copies string value into AI input fields with click highlight scale animations.
* **Accessibility**: Tooltips detailing command effects; elements accessible in sequence via keyboard tabs.
* **State Mappings**: Populated based on active page contexts (e.g., highlights carbon templates in Carbon page).

---

## 8. Explainability & Evidence Components

### 8.1 Evidence Panel
* **Properties**: Source document links, validation certificates, system logs, verified signature indicators.
* **Inputs/Outputs**:
  * *Input*: `evidenceRecords: List<EvidenceItem>`.
  * *Output*: `onVerifySignature(item: EvidenceItem)`.
* **Interactive Behaviors**: File icons display verification status details on mouse hovers; download actions animate click targets.
* **Accessibility**: Label descriptions for document status indicators; screen readers parse download actions.
* **State Mappings**: Syncs with audit ledger events in real-time.

### 8.2 Methodology Drawer
* **Properties**: Side drawer panel, mathematical formulas, data collection methods, ecoinvent databases, emission factor sources.
* **Inputs/Outputs**:
  * *Input*: `formulaReference: String`, `isOpen: Boolean`.
  * *Output*: `onCloseDrawer()`.
* **Interactive Behaviors**: Slides in horizontally from right viewport border; page backdrop dims automatically.
* **Accessibility**: `aria-modal="true"`, focus is trapped in drawer container while open; Escape key triggers close action.
* **State Mappings**: Displays default formula values aligned with carbon calculation choices.

### 8.3 Explainability Panel
* **Properties**: Highlighted logic trees, feature impact scores, decision metrics, plain-text explanations.
* **Inputs/Outputs**:
  * *Input*: `modelDecision: Object`, `featureWeights: List<Weight>`.
  * *Output*: `onFeatureSelect(featureId: String)`.
* **Interactive Behaviors**: Feature weight bar graph animations; interactive nodes expand on user selection.
* **Accessibility**: Backing numerical details listed inside a data table format next to charts.
* **State Mappings**: Linked with active process discovery variant selections.

---

## 9. Reporting & Score Cards

### 9.1 Audit Trail Viewer
* **Properties**: Activity timeline component, event details dropdown, user identity badges, timestamp logs.
* **Inputs/Outputs**:
  * *Input*: `auditEvents: List<AuditEvent>`, `filters: Object`.
  * *Output*: `onRowClick(eventId: String)`.
* **Interactive Behaviors**: Timeline items expand inline to display metadata details; filtering terms animate list views.
* **Accessibility**: `role="feed"`, timeline objects ordered chronologically with voice descriptions.
* **State Mappings**: Keeps active timeline filters saved to prevent state reset on page navigation.

### 9.2 Supplier Card
* **Properties**: Supplier name, logo, location badge, risk score index, carbon intensity indicator, average delay metrics.
* **Inputs/Outputs**:
  * *Input*: `supplierData: SupplierProfile`.
  * *Output*: `onToggleFavorite()`, `onSupplierSelect()`.
* **Interactive Behaviors**: Action links hover-underline; card outlines map to Supplier's risk colors on selection.
* **Accessibility**: High-contrast indicator text labels (AAA contrast compliant).
* **State Mappings**: Maintains selected supplier dashboard focus on workspace navigation.

### 9.3 ESG Score Card
* **Properties**: ESG overall grade letter, Environmental/Social/Governance sub-metric breakdown dials, regulatory compliance statuses.
* **Inputs/Outputs**:
  * *Input*: `esgData: ESGMetrics`, `activeFramework: String`.
  * *Output*: `onInspectFramework()`.
* **Interactive Behaviors**: Radial dial metrics fill on load; hover details show raw values compared to target values.
* **Accessibility**: Standard text backups for visual radial charts.
* **State Mappings**: Changes automatically depending on selected framework settings.

### 9.4 Carbon Score Card
* **Properties**: Global footprint indicator, Scope 1/2/3 categorization, reduction target indicators.
* **Inputs/Outputs**:
  * *Input*: `carbonData: CarbonMetrics`, `thresholds: Object`.
  * *Output*: `onToggleScopes()`.
* **Interactive Behaviors**: Click actions toggle target lines on graph; progress indicators pulse if emission limits are exceeded.
* **Accessibility**: `aria-live` declarations update if calculations change based on range controls.
* **State Mappings**: Refreshes data parameters on active workspace filtering.

---

## 10. Presentation Components

### 10.1 Presentation Slide Component
* **Properties**: Viewport slide canvas frame, interactive widget areas, side presenter controls, slide transition layer.
* **Inputs/Outputs**:
  * *Input*: `slideContent: SlideLayout`, `isLiveConnect: Boolean`.
  * *Output*: `onSlideTransition(direction: 'next' | 'prev')`, `onDataSyncToggle()`.
* **Interactive Behaviors**: Smooth slide transitions; embedded charts retain full tooltips and panning behaviors.
* **Accessibility**: Support for screen readers during presentation flow; full keyboard shortcuts (Space/Arrows) map to page controls.
* **State Mappings**: Live Connect states are persisted across slides; slide number stored in temporary session storage.
