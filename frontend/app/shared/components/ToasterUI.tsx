import { Toaster } from "react-hot-toast";

export const ToasterUI = () => (
  <Toaster
    position="top-left"
    gutter={8}
    toastOptions={{
      duration: 3000,

      // Общий стиль
      style: {
        background: "#ffffff",
        color: "#111111",
        border: "1px solid #e5e5e5",
        borderRadius: "12px",
        padding: "8px 16px",
        boxShadow:
          "0 10px 16px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
        fontSize: "16px",
        maxWidth: "480px",
      },

      success: {
        iconTheme: {
          primary: "#10b981",
          secondary: "#ffffff",
        },
        style: {
          borderColor: "#10b981",
        },
      },

      error: {
        iconTheme: {
          primary: "#ef4444",
          secondary: "#ffffff",
        },
        style: {
          borderColor: "#ef4444",
        },
      },
    }}
  />
);
