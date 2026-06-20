# SustainOCPM Page Specifications

This document defines the structural configurations, state behaviors, and interface specifications for the 12 core pages of the SustainOCPM platform, referencing components defined in [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) and tokens in [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md).

---

## 1. Home Page

### Purpose & User Persona
* **Purpose**: Primary workspace setup hub, log upload interface, and schema mapping configuration workbench.
* **User Persona**: ESG Analyst, Process Engineer, Operations Manager.

### Primary Goals & KPIs
* **Goals**: Successfully ingest raw event data logs, map structural headers to OCEL 2.0 schemas, and navigate to the analysis workspace.
* **KPIs**: Ingestion Success Rate (>99.5%), Mapping Efficiency (<2 mins setup).

### Inputs & Outputs
* **Inputs**: User-provided log files (OCEL 2.0 JSON/XML, CSV files), database workspace lists.
* **Outputs**: Formatted, verified database tables, schema mapping configurations.

### Components Used
* `Navigation Bar`, `Upload Wizard`, `Schema Mapping Wizard`, `Data Table`, `Alert Panel`.

### User Interactions
* Drag-and-drop log upload selection.
* Drag-and-drop or select column dropdown mapping links.
* Click workspace items to navigate.

### Dependencies
* Database log-ingestion APIs, workspace inventory services, local validator modules.

### Persisted State & Session State
* **Persisted State**: Workspace list, previous schema mapping templates, active workspace preference.
* **Session State**: Uploaded file metadata, active upload progress, validation warnings.
* *Note: Log content mapping setups are saved to LocalStorage to prevent loss on browser reload.*

### Navigation & Refresh Behavior
* **Navigation**: Loads active Dashboard on confirm. Back returns to landing selection.
* **Refresh**: Restores pending file upload status.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Ingestion pane displays a placeholder message: "No log file uploaded yet."
* **Loading**: Spinner overlay displaying progress: "Parsing log database structures..."
* **Error**: Alert panel displays parser errors: "Invalid OCEL 2.0 formatting detected on line 14."
* **First-Time**: Interactive checklist guiding the user to upload a sample CSV/JSON log.

### Layout Specifications
* **Desktop**: 2-column view (Ingestion/Mapping in 8 cols; Status & Help in 4 cols).
* **Tablet**: Stacked single-column view. Map canvas features scroll viewports.
* **Mobile**: Simplified list view. Displays warning recommending desktop view for mapping.

### Accessibility Considerations
* Form inputs mapped to `<label>` fields. Screen reader announcements on file verification checks.

---

## 2. Dashboard Page

### Purpose & User Persona
* **Purpose**: High-level platform operations, sustainability KPIs, and process health overview.
* **User Persona**: Sustainability Director, Operations Executive.

### Primary Goals & KPIs
* **Goals**: Monitor operational metrics, evaluate ESG conformity, and identify high-carbon process paths.
* **KPIs**: Lead Time reduction, Carbon Footprint vs. Offset Targets, ESG Fitness rate.

### Inputs & Outputs
* **Inputs**: Aggregated log data, target threshold levels, time-range parameters.
* **Outputs**: Real-time widget rendering, exported PDF performance summaries.

### Components Used
* `Navigation Bar`, `Sidebar`, `Breadcrumbs`, `Metric Card`, `Process Graph` (Summary), `Chart Container`, `Recommendation Panel`.

### User Interactions
* Time filter adjustment dropdown selections.
* Clicking recommendation cards.
* Hovering over trend lines to show values.

### Dependencies
* Aggregation database APIs, carbon footprint calculation engine.

### Persisted State & Session State
* **Persisted State**: Active workspace settings, user interface settings, active time filter.
* **Session State**: Dashboard export progress, recommendation panel dismissal history.

### Navigation & Refresh Behavior
* **Navigation**: Clicking the dashboard summary flow graph redirects to Process Discovery.
* **Refresh**: Retains the chosen timeline scope and workspace selection.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Placeholder cards displaying: "No data available. Please upload a log."
* **Loading**: Shimmer loader states on widgets while processing metrics.
* **Error**: Widget overlays showing: "Failed to connect to database. Retrying..."
* **First-Time**: Onboarding popups pointing to the filter tools and global settings.

### Layout Specifications
* **Desktop**: Grid-based flow (KPI metrics top; 8-col graph center; 4-col recommendations right).
* **Tablet**: KPI cards in a 2x2 grid; graphs and recommendations stacked vertically.
* **Mobile**: Single-column layout. Sidebar collapses into a hamburger icon menu.

### Accessibility Considerations
* Dynamic chart labels provide alt text descriptions. High contrast rating dials (minimum 4.5:1 ratio).

---

## 3. Process Discovery Page

### Purpose & User Persona
* **Purpose**: Advanced explorer for discovering actual processes, variant paths, and operational bottlenecks.
* **User Persona**: Process Mining Consultant, Operations Manager.

### Primary Goals & KPIs
* **Goals**: Analyze multi-object OCPM models, isolate paths, and find process bottlenecks.
* **KPIs**: Process Throughput Rate, Discovery Variant Count, Bottleneck Latency (Hours).

### Inputs & Outputs
* **Inputs**: Event log data, node threshold filters, selected object categories (e.g., Order, Item).
* **Outputs**: Interactive OCPM process graphs, filtered data instances lists.

### Components Used
* `Navigation Bar`, `Sidebar`, `Process Graph`, `Data Table`, `Explainability Panel`.

### User Interactions
* Adjusting threshold slider values to clean graph views.
* Clicking nodes/edges to select them.
* Toggling visibility parameters on target object types.

### Dependencies
* Object-Centric Process Mining (OCPM) model generators, path path-calculation APIs.

### Persisted State & Session State
* **Persisted State**: Graph zoom configurations, filter selections, active object type visibility.
* **Session State**: Selected node focus state, active variant path filter, pagination details.

### Navigation & Refresh Behavior
* **Navigation**: Focus node detail opens bottom event data logs. Transition button links to Conformance.
* **Refresh**: Retains zoom coordinates and graph layout structure.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Message: "No process variants discovered for this selection."
* **Loading**: Spinner overlay showing: "Rendering process map nodes..."
* **Error**: Overlay: "Out of memory rendering complex process graph. Please adjust filters."
* **First-Time**: Help overlays explaining zoom, pan, and node-filtering controls.

### Layout Specifications
* **Desktop**: Persistent sidebar navigation, 9-col process graph viewport, 3-col variant list pane.
* **Tablet**: Collapsed sidebar, horizontal layout splits split between canvas and variant selectors.
* **Mobile**: Graph view hidden with message: "OCPM graph requires a wider screen. Switching to tabular view."

### Accessibility Considerations
* Graph zoom actions controllable via keyboard keys. Alternative raw data table always switchable.

---

## 4. Conformance Intelligence Page

### Purpose & User Persona
* **Purpose**: Process compliance auditing, identifying process variations and compliance breaches.
* **User Persona**: Internal Audit Lead, Quality Control Auditor.

### Primary Goals & KPIs
* **Goals**: Map discovered processes against BPMN reference maps, flag SLA violations, and record audit details.
* **KPIs**: Process Fitness, Precision Index, Conformant Cases %, SLA Violation rate.

### Inputs & Outputs
* **Inputs**: Actual log files, reference BPMN 2.0 models, deviation rules.
* **Outputs**: Discrepancy logs, conformance models, verification records.

### Components Used
* `Navigation Bar`, `Sidebar`, `Metric Card`, `Process Graph` (Conformance Overlay), `Data Table`, `Alert Panel`, `Audit Trail Viewer`.

### User Interactions
* Ingesting reference target models.
* Hovering process paths to read deviation flags.
* Selecting discrepancy rows to audit transactions.

### Dependencies
* Conformance checking engines (token replication / alignment calculations).

### Persisted State & Session State
* **Persisted State**: Reference BPMN files, compliance definitions.
* **Session State**: Mapped deviation logs, current severity classifications.

### Navigation & Refresh Behavior
* **Navigation**: Clicking an audited case navigates to Process Discovery for verification.
* **Refresh**: Restores uploaded compliance models and keeps filters.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "No deviations detected. Platform is 100% compliant."
* **Loading**: Spinner: "Aligning process logs against reference BPMN model..."
* **Error**: Alert: "BPMN model version mismatch. Please re-upload conforming schema."
* **First-Time**: Visual call-to-action to import a reference BPMN process file.

### Layout Specifications
* **Desktop**: Side-by-side view (8-col comparative graph, 4-col severity timeline and alert desk).
* **Tablet**: Graph on top; compliance tables stacked underneath.
* **Mobile**: Stacked tables focusing exclusively on high-severity deviation lists.

### Accessibility Considerations
* Compliance visual markers use secondary icon badges in addition to standard colors (green/red).

---

## 5. Carbon Intelligence Page

### Purpose & User Persona
* **Purpose**: Process carbon footprint attribution, Scope 1/2/3 mapping, and carbon hotspot mitigation.
* **User Persona**: Sustainability Lead, Operations Analyst.

### Primary Goals & KPIs
* **Goals**: Pinpoint process steps generating high emissions, run cleanup scenarios, and report footprints.
* **KPIs**: Carbon intensity (tCO2e/unit), Scope 1/2/3 footprints, mitigation savings.

### Inputs & Outputs
* **Inputs**: Log events, Ecoinvent databases, emission factors, simulator parameters.
* **Outputs**: Carbon process flow maps, simulated footprints, mitigation reports.

### Components Used
* `Navigation Bar`, `Sidebar`, `Metric Card`, `Process Graph` (Carbon-weighted), `Chart Container`, `Scenario Simulator`, `Methodology Drawer`.

### User Interactions
* Toggling Scope 1, 2, and 3 settings on/off.
* Moving sliders in the simulator to evaluate carbon changes.
* Opening details drawers to inspect calculations.

### Dependencies
* Environmental databases (Ecoinvent), Carbon calculator APIs.

### Persisted State & Session State
* **Persisted State**: Active Scope selection, simulator presets, emission factor selections.
* **Session State**: Output results, drawer open/closed status, active formula details.

### Navigation & Refresh Behavior
* **Navigation**: Redirect to Supplier page for supplier mitigation choices.
* **Refresh**: Caches and restores current simulation parameters.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Overlay: "No carbon attributes matched. Check mapping settings."
* **Loading**: Spinner: "Calculating Scope 1/2/3 process emissions footprint..."
* **Error**: Alert: "Calculation error: Missing emission factors for resource X."
* **First-Time**: Interactive tutorial explaining Scope 1/2/3 classifications.

### Layout Specifications
* **Desktop**: 12-column layout split: 8-col carbon graph and 4-col interactive simulator panel.
* **Tablet**: Graph on top, simulator inputs below.
* **Mobile**: High-level carbon scorecards and basic mitigation tables.

### Accessibility Considerations
* Colorblind-safe color schemes for carbon graphs (accessible indexes). Focus indicator outlines on sliders.

---

## 6. ESG Intelligence Page

### Purpose & User Persona
* **Purpose**: Performance metric tracking against ESG standards (GRI, SASB, TCFD, CSRD).
* **User Persona**: Corporate ESG Auditor, Sustainability Lead.

### Primary Goals & KPIs
* **Goals**: Compile framework-compliant reporting cards, review evidence logs, and verify compliance.
* **KPIs**: GRI Standard Coverage, Governance Score index, Social Equity Index.

### Inputs & Outputs
* **Inputs**: Selected ESG reporting frameworks, process metrics data, third-party documents.
* **Outputs**: ESG score reports, audited compliance statements.

### Components Used
* `Navigation Bar`, `Sidebar`, `ESG Score Card`, `Data Table`, `Evidence Panel`.

### User Interactions
* Shifting frameworks using dropdown selectors.
* Inspecting evidence files by clicking links.
* Toggling compliance parameter scopes.

### Dependencies
* ESG standards metadata databases, document storage systems.

### Persisted State & Session State
* **Persisted State**: Active regulatory framework selection, audit filters.
* **Session State**: Evidence validation results, file preview parameters.

### Navigation & Refresh Behavior
* **Navigation**: Link transitions verify supplier credentials inside the Supplier portal.
* **Refresh**: Restores active reporting framework layouts.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "No indicators mapped for chosen framework. Define targets."
* **Loading**: Spinner: "Compiling ESG metric summaries and evidence folders..."
* **Error**: Overlay: "Missing credentials to access the document storage server."
* **First-Time**: Highlights framework selection options to initialize audit profiles.

### Layout Specifications
* **Desktop**: ESG cards on top (12-col); detailed indicator grid below.
* **Tablet**: Accordion view categorizing Environmental, Social, and Governance rows.
* **Mobile**: Grid rows collapse to display simplified compliance checklists.

### Accessibility Considerations
* Verification status indicators use text descriptors alongside color icons. Tab navigation for table rows.

---

## 7. Supplier Intelligence Page

### Purpose & User Persona
* **Purpose**: Analyzing supplier risks, shipping carbon footprints, and logistics performance.
* **User Persona**: Procurement Lead, Logistics Director.

### Primary Goals & KPIs
* **Goals**: Rank supplier performance, discover transit chain deviations, and evaluate suppliers.
* **KPIs**: Supplier Carbon Intensity, Delivery Delay (Hours), Compliance rating.

### Inputs & Outputs
* **Inputs**: Supplier directories, shipping transit records, environmental audit files.
* **Outputs**: Supplier comparison matrices, risk cards, transit carbon maps.

### Components Used
* `Navigation Bar`, `Sidebar`, `Supplier Card`, `Benchmark Card`, `Process Graph` (Logistics), `Data Table`.

### User Interactions
* Clicking supplier cards to view metrics.
* Drag-and-drop comparison inputs.
* Panning supply chain logistics maps.

### Dependencies
* Supplier logistics APIs, GIS mapping engines.

### Persisted State & Session State
* **Persisted State**: Selected supplier focus, comparison groupings.
* **Session State**: active filters, comparison panel toggles.

### Navigation & Refresh Behavior
* **Navigation**: Clicking map logistics nodes opens path details in Process Discovery.
* **Refresh**: Retains the chosen supplier profile focus.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "No suppliers matched the chosen parameters."
* **Loading**: Shimmer loader cards rendering supplier profile data.
* **Error**: Message: "Failed to connect to supplier metrics database."
* **First-Time**: Guide highlights the "Compare Suppliers" tool in the sidebar area.

### Layout Specifications
* **Desktop**: 3-col supplier scroll view left, 9-col analytics and logistics workspace right.
* **Tablet**: Top scroll view selector, metrics stacked below.
* **Mobile**: Single-column view focusing on supplier lists; profile page details load in fullscreen overlays.

### Accessibility Considerations
* Risk rating badges (red, orange, green) use AAA text contrast tokens. Accessible map controls.

---

## 8. BRSR Reporting Page

### Purpose & User Persona
* **Purpose**: Compiling SEBI-mandated BRSR sustainability reports for Indian listed companies.
* **User Persona**: Compliance Officer, Company ESG Auditor.

### Primary Goals & KPIs
* **Goals**: Auto-populate BRSR survey questions, resolve data discrepancies, and export XBRL files.
* **KPIs**: BRSR Completion percentage, Validation Error count, Inferred Metric accuracy.

### Inputs & Outputs
* **Inputs**: Log data tables, manual text fields, previous BRSR templates.
* **Outputs**: Validated BRSR reports, regulatory XBRL compliance documents.

### Components Used
* `Navigation Bar`, `Sidebar`, `Report Viewer`, `Alert Panel`, `Audit Trail Viewer`.

### User Interactions
* Clicking auto-populate buttons.
* Typing manual indicators into data sheets.
* Toggling validation checkers.

### Dependencies
* BRSR regulatory templates (SEBI), XBRL format translators.

### Persisted State & Session State
* **Persisted State**: Saved questionnaire draft answers, manual entries.
* **Session State**: Validation warning list, current step index.
* *Note: Draft answers are autosaved to database storage every 30 seconds.*

### Navigation & Refresh Behavior
* **Navigation**: Next/Prev step buttons. Cancel returns to Home page dashboard.
* **Refresh**: Loads active step and pre-fills completed fields without data loss.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Setup screen: "Click 'Auto-Populate' to build draft from process log data."
* **Loading**: Spinner: "Mapping operational data to BRSR questionnaire sections..."
* **Error**: Alert: "Validation check failed: Missing energy values in Section C."
* **First-Time**: Highlights step-by-step progress flow markers to initialize draft setup.

### Layout Specifications
* **Desktop**: 8-col interactive questionnaire viewer left, 4-col validation sidebar right.
* **Tablet**: Stacked layout. Error sidebar collapses to a sliding tray drawer.
* **Mobile**: Displays warning recommending desktop view for document compilation.

### Accessibility Considerations
* Clear keyboard tab indexing on form inputs. ARIA alert targets highlight errors.

---

## 9. AI Copilot Page

### Purpose & User Persona
* **Purpose**: Interactive conversation workspace to analyze process metrics and request advice.
* **User Persona**: ESG Analyst, Operations Director, Process Engineer.

### Primary Goals & KPIs
* **Goals**: Ask process mining questions in natural language, explain bottlenecks, and generate reports.
* **KPIs**: Query Resolution speed, Recommendation quality, Automation accuracy.

### Inputs & Outputs
* **Inputs**: User chat queries, workspace datasets, attached process maps, filters.
* **Outputs**: Agent responses, analysis tables, recommendations, python code blocks.

### Components Used
* `Navigation Bar`, `Sidebar`, `AI Chat`, `Prompt Suggestions`, `Explainability Panel`.

### User Interactions
* Submitting queries.
* Selecting command templates.
* Attaching charts/graphs to chat inputs.

### Dependencies
* LLM integrations, multi-agent frameworks, vector search systems.

### Persisted State & Session State
* **Persisted State**: Chat message history thread, attached dataset references.
* **Session State**: Processing status indicators, cursor positioning.
* *Note: Chat history is persistent to allow continued conversation across screens.*

### Navigation & Refresh Behavior
* **Navigation**: Navigating pages retains chat history inside sidebar views.
* **Refresh**: Reloads conversation history.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: UI shows welcome assistant prompt: "How can I analyze your process today?"
* **Loading**: Chat indicator showing: "Copilot agent is analyzing log database..."
* **Error**: Chat message bubble: "Network timeout. Click here to resend query."
* **First-Time**: Suggests simple starting queries like "/explain-bottlenecks".

### Layout Specifications
* **Desktop**: Split-view layout: 8-col chat thread workspace, 4-col suggestions and context.
* **Tablet**: Chat workspace spans full screen width; context slides out in side drawer.
* **Mobile**: Simplified chat window; attachments minimized to badge icons.

### Accessibility Considerations
* Log regions use `aria-live="polite"`. Inputs allow speech-to-text integration.

---

## 10. Presentation Mode Page

### Purpose & User Persona
* **Purpose**: Slides-based workspace designed for sustainability performance reviews.
* **User Persona**: Sustainability Executive, External Auditor.

### Primary Goals & KPIs
* **Goals**: Deliver interactive process performance reviews with live database connections.
* **KPIs**: Slide Load Time, Live Query latency, Presentation clarity.

### Inputs & Outputs
* **Inputs**: Slide deck files, cached metrics, live DB connections.
* **Outputs**: Visual slide rendering, updated database logs.

### Components Used
* `Presentation Slide Component`, `Process Graph`, `Metric Card`, `Chart Container`.

### User Interactions
* Arrow key slide controls.
* Panning and zooming maps on slide pages.
* Toggling live connection switches.

### Dependencies
* Slide engines, database synchronizers.

### Persisted State & Session State
* **Persisted State**: Slide content templates, deck arrangements.
* **Session State**: Active slide index, live-connect toggle status.

### Navigation & Refresh Behavior
* **Navigation**: Exit slide button returns focus to the main Dashboard.
* **Refresh**: Opens presentation on the active slide page.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "No slides imported. Drag template to start presentation."
* **Loading**: Spinner: "Initializing live database connector queries..."
* **Error**: Overlay: "Lost live connection. Reverting to cached slide data."
* **First-Time**: Help overlay explaining keyboard slide shortcut keys.

### Layout Specifications
* **Desktop**: Fullscreen layout with presenter control overlays (1024px+).
* **Tablet**: Presenter sidebar left, slide panel center.
* **Mobile**: Simple list view showing static snapshots of slide decks.

### Accessibility Considerations
* Full screen reader access. Clear high-contrast colors (3:1 minimum for controls).

---

## 11. Documentation Page

### Purpose & User Persona
* **Purpose**: User manuals, regulatory framework guidelines, and academic reference papers.
* **User Persona**: Process Mining Researcher, ESG Consultant.

### Primary Goals & KPIs
* **Goals**: Locate system manuals, research methodologies, and verify carbon calculation logic.
* **KPIs**: Page Load time, Search result accuracy, User usage time.

### Inputs & Outputs
* **Inputs**: Markdown documentation, query strings.
* **Outputs**: Markdown guides, reference link selections.

### Components Used
* `Navigation Bar`, `Sidebar`, `Knowledge Base Viewer`.

### User Interactions
* Typing search parameters.
* Clicking article directory categories.
* Scrolling through reference docs.

### Dependencies
* Help desk CMS, markdown parsers, math equation engines.

### Persisted State & Session State
* **Persisted State**: Saved bookmarks, recently viewed docs.
* **Session State**: Search terms, folder tree expansion status.

### Navigation & Refresh Behavior
* **Navigation**: Internal links jump to documentation pages.
* **Refresh**: Keeps current chapter view active.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "Search query returned 0 results. Try different keywords."
* **Loading**: Skeleton lines loading document layout.
* **Error**: Alert: "Unable to parse document markdown resource."
* **First-Time**: Displays "Platform Quick Start Guide" on the landing layout.

### Layout Specifications
* **Desktop**: 3-col directory tree navigation left, 9-col markdown document reader right.
* **Tablet**: Directory collapses into top navigation menu.
* **Mobile**: Fullscreen reading layout; directory opens from overlay toggle.

### Accessibility Considerations
* Tree menus use ARIA navigation roles. Math formulas provide alternative descriptions.

---

## 12. Settings Page

### Purpose & User Persona
* **Purpose**: Workspace configurations, API setups, team access, and integrations.
* **User Persona**: System Administrator, ESG Architect.

### Primary Goals & KPIs
* **Goals**: Configure ERP connectors, set up database credentials, and manage API keys.
* **KPIs**: Integration Status Success, Key generation time.

### Inputs & Outputs
* **Inputs**: API keys, connection settings, theme settings.
* **Outputs**: API key validations, connection statuses.

### Components Used
* `Navigation Bar`, `Sidebar`, `Data Table`, `Alert Panel`.

### User Interactions
* Inputting connection credentials.
* Clicking connection sync controls.
* Generating API tokens.

### Dependencies
* External database connectors, platform auth tools.

### Persisted State & Session State
* **Persisted State**: Integration tokens, connection hosts, theme choices.
* **Session State**: Active connection check responses.

### Navigation & Refresh Behavior
* **Navigation**: Save commits changes and returns to Dashboard.
* **Refresh**: Keeps settings edits intact.

### States (Empty, Loading, Error, First-Time User)
* **Empty**: Text: "No ERP connections linked. Click 'Add Connection'."
* **Loading**: Spinner: "Verifying ERP database server link..."
* **Error**: Alert: "Invalid host address or credentials."
* **First-Time**: Highlights input forms to set up database links.

### Layout Specifications
* **Desktop**: Tabbed layout (Category panel 3-col; Form controls 9-col).
* **Tablet**: Top horizontal category selector; form stacked below.
* **Mobile**: Stacks category choices and input tables vertically.

### Accessibility Considerations
* Focus rings on interactive inputs. Access tokens have hidden view toggles.
