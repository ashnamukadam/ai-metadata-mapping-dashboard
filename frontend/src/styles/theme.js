import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    background: {
      default: "#FFF8DC",
      paper: "#FFFDF4",
    },
    primary: {
      main: "#8B5E3C",
    },
    secondary: {
      main: "#D8C59F",
    },
    text: {
      primary: "#5C4033",
      secondary: "#7A5C4D",
    },
  },

  typography: {
    fontFamily: "Poppins, Arial, sans-serif",

    h4: {
      fontWeight: 700,
      color: "#5C4033",
    },

    h5: {
      fontWeight: 600,
      color: "#5C4033",
    },

    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },

  shape: {
    borderRadius: 12,
  },
});

export default theme;