import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  // Strict mode not working with socket
  <React.Fragment>
    <App />
  </React.Fragment>
)
