import axios from "axios";

// const API_URL = "http://13.51.171.153:5000";
// const API_URL = "http://localhost:8001";
const API_URL = "http://16.170.98.127:8001";

const api = {
  // Health check
  healthCheck: async () => {
    try {
      const response = await axios.get(`${API_URL}/status`);
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  },

  // Upload and process Excel file directly with optimizations
  uploadAndProcessFile: async (file, options = {}) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log("🚀 Starting optimized file upload...");
      const startTime = Date.now();

      const response = await axios.post(`${API_URL}/upload_excel/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: options.timeout || 120000, // 2 minute default timeout
        signal: options.signal, // Support for AbortController
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`📤 Upload progress: ${percentCompleted}%`);
        },
      });

      const processingTime = (Date.now() - startTime) / 1000;
      console.log(`⚡ Processing completed in ${processingTime.toFixed(2)}s`);

      return response.data;
    } catch (error) {
      console.error("❌ File upload and processing failed:", error);
      throw error;
    }
  },

  // Get all insights (sheet, general, and additional)
  getAllInsights: async () => {
    try {
      const response = await axios.get(`${API_URL}/all_insights`);
      return response.data;
    } catch (error) {
      console.error("Failed to get all insights:", error);
      throw error;
    }
  },

  // Generate additional insights from the data
  generateMoreInsights: async () => {
    try {
      const response = await axios.post(`${API_URL}/generate_more_insights`);
      return response.data;
    } catch (error) {
      console.error("Generating additional insights failed:", error);
      throw error;
    }
  },

  // Get individual sheet insights for deep dive
  getSheetInsights: async () => {
    try {
      const response = await axios.get(`${API_URL}/sheet_insights`);
      return response.data;
    } catch (error) {
      console.error("Getting sheet insights failed:", error);
      throw error;
    }
  },

  // Save user feedback (simplified implementation)
  saveFeedback: async (_, feedback) => {
    try {
      console.log("Saving feedback:", feedback);
      return { success: true };
    } catch (error) {
      console.error("Saving feedback failed:", error);
      throw error;
    }
  },

  // Send email with insights (simplified implementation)
  sendEmail: async (_, emailData) => {
    try {
      // Simulate a delay
      await new Promise((resolve) => setTimeout(resolve, 1500));
      console.log("Sending email with data:", emailData);
      return { success: true, message: "Email sent successfully" };
    } catch (error) {
      console.error("Email sending failed:", error);
      throw error;
    }
  },

  // Download insights files
  downloadInsights: async () => {
    try {
      const response = await axios.get(`${API_URL}/download/insights`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error("Download insights failed:", error);
      throw error;
    }
  },

  downloadGeneralInsights: async () => {
    try {
      const response = await axios.get(`${API_URL}/download/general`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error("Download general insights failed:", error);
      throw error;
    }
  },

  downloadAdditionalInsights: async () => {
    try {
      const response = await axios.get(`${API_URL}/download/additional_insights`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error("Download additional insights failed:", error);
      throw error;
    }
  },
};

export default api;
