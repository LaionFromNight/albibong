import { useContext, useEffect } from "react";
import {
  Navigate,
  Outlet,
  RouterProvider,
  createBrowserRouter,
} from "react-router-dom";
import Navigation from "./components/Navigation";
import Radar from "./pages/Radar";
import WebsocketProvider, {
  WebsocketContext,
} from "./providers/WebsocketProvider";
import WorldProvider, { WorldContext } from "./providers/WorldProvider";
import { theme } from "./theme";

const App = () => {
  return (
    <WebsocketProvider>
      <WorldProvider>
        <Init>
          <Router />
        </Init>
      </WorldProvider>
    </WebsocketProvider>
  );
};

const container = {
  width: "100%",
  padding: "96px 64px 64px 128px",
  backgroundColor: theme.palette.background.default,
  minHeight: "100vh",
};

const Layout = () => {
  return (
    <>
      <Navigation />
      <div style={container}>
        <Outlet />
      </div>
    </>
  );
};

const Router = () => {
  const router = createBrowserRouter([
    {
      path: "/",
      element: <Layout />,
      children: [
        {
          index: true,
          element: <Radar />,
        },
        {
          path: "/radar",
          element: <Radar />,
        },
        {
          path: "/dps-marker",
          element: <Navigate replace to="/radar" />,
        },
      ],
    },
  ]);
  return <RouterProvider router={router} />;
};

const Init = ({ children }: { children: React.ReactNode }) => {
  const { lastMessage } = useContext(WebsocketContext);
  const {
    initPlayer,
    initWorld,
    updateHealthCheck,
    updateLocation,
    updateRadarPosition,
    updateRadarWidget,
  } = useContext(WorldContext);

  useEffect(() => {
    if (lastMessage !== null) {
      const ws_event = JSON.parse(lastMessage.data);
      if (ws_event.type == "init_world") {
        initWorld(ws_event.payload.me, ws_event.payload.world);
      } else if (ws_event.type == "init_character") {
        initPlayer(ws_event.payload);
      } else if (ws_event.type == "health_check") {
        updateHealthCheck(ws_event.payload);
      } else if (ws_event.type == "update_location") {
        updateLocation(ws_event.payload.map, ws_event.payload.isInDungeon);
      } else if (ws_event.type == "radar_update") {
        updateRadarWidget(ws_event.payload);
      } else if (ws_event.type == "radar_position_update") {
        updateRadarPosition(
          ws_event.payload.position.x,
          ws_event.payload.position.y
        );
      }
    }
  }, [lastMessage]);

  return <>{children}</>;
};

export default App;
