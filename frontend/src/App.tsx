import { Component, type ErrorInfo, type ReactNode } from "react";
import Dashboard from "./components/dashboard/Dashboard";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ color: "#ff3366", padding: 40, fontFamily: "monospace" }}>
          <h1>Render Error</h1>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 14 }}>
            {this.state.error.message}
          </pre>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 11, color: "#888", marginTop: 16 }}>
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
