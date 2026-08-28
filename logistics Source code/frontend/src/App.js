import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import DashboardLayout from "@/components/DashboardLayout";

import Landing from "@/pages/Landing";
import Login from "@/pages/auth/Login";
import Register from "@/pages/auth/Register";
import ForgotPassword from "@/pages/auth/ForgotPassword";
import ResetPassword from "@/pages/auth/ResetPassword";

import Dashboard from "@/pages/Dashboard";
import Shipments from "@/pages/Shipments";
import ShipmentDetail from "@/pages/ShipmentDetail";
import RiskIntelligence from "@/pages/RiskIntelligence";
import CustomsIntelligence from "@/pages/CustomsIntelligence";
import Geopolitical from "@/pages/Geopolitical";
import ImpactAnalysis from "@/pages/ImpactAnalysis";
import Simulator from "@/pages/Simulator";
import RouteOptimizer from "@/pages/RouteOptimizer";
import Recovery from "@/pages/Recovery";
import Compliance from "@/pages/Compliance";
import Analytics from "@/pages/Analytics";
import ModelLearning from "@/pages/ModelLearning";
import Reports from "@/pages/Reports";
import Alerts from "@/pages/Alerts";
import Integrations from "@/pages/Integrations";
import Settings from "@/pages/Settings";

// AI Business Automation Copilot pages
import AutomationCopilot from "@/pages/AutomationCopilot";
import WorkflowStudio from "@/pages/WorkflowStudio";
import AutomationOpportunities from "@/pages/AutomationOpportunities";
import ConflictCenter from "@/pages/ConflictCenter";
import AutomationInsights from "@/pages/AutomationInsights";

const Shell = ({ children }) => (
  <ProtectedRoute>
    <DashboardLayout>{children}</DashboardLayout>
  </ProtectedRoute>
);

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <AuthProvider>
        <Toaster richColors position="top-right" theme="dark" />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            <Route path="/app/dashboard" element={<Shell><Dashboard /></Shell>} />
            <Route path="/app/shipments" element={<Shell><Shipments /></Shell>} />
            <Route path="/app/shipments/:id" element={<Shell><ShipmentDetail /></Shell>} />
            <Route path="/app/risk" element={<Shell><RiskIntelligence /></Shell>} />
            <Route path="/app/customs" element={<Shell><CustomsIntelligence /></Shell>} />
            <Route path="/app/geopolitical" element={<Shell><Geopolitical /></Shell>} />
            <Route path="/app/impact" element={<Shell><ImpactAnalysis /></Shell>} />
            <Route path="/app/simulator" element={<Shell><Simulator /></Shell>} />
            <Route path="/app/routes" element={<Shell><RouteOptimizer /></Shell>} />
            <Route path="/app/recovery" element={<Shell><Recovery /></Shell>} />
            <Route path="/app/compliance" element={<Shell><Compliance /></Shell>} />
            <Route path="/app/analytics" element={<Shell><Analytics /></Shell>} />
            <Route path="/app/model-learning" element={<Shell><ModelLearning /></Shell>} />
            <Route path="/app/reports" element={<Shell><Reports /></Shell>} />
            <Route path="/app/alerts" element={<Shell><Alerts /></Shell>} />
            <Route path="/app/integrations" element={<Shell><Integrations /></Shell>} />
            <Route path="/app/settings" element={<Shell><Settings /></Shell>} />

            {/* AI Business Automation Copilot */}
            <Route path="/app/copilot" element={<Shell><AutomationCopilot /></Shell>} />
            <Route path="/app/workflows" element={<Shell><WorkflowStudio /></Shell>} />
            <Route path="/app/opportunities" element={<Shell><AutomationOpportunities /></Shell>} />
            <Route path="/app/conflicts" element={<Shell><ConflictCenter /></Shell>} />
            <Route path="/app/automation-insights" element={<Shell><AutomationInsights /></Shell>} />

            <Route path="/app" element={<Navigate to="/app/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
