import { AuthGate } from "./AuthGate";
import InteractionNew from "./pages/InteractionNew";

export default function App() {
  return (
    <AuthGate>
      {({ account, onLogout }) => (
        <InteractionNew account={account} onLogout={onLogout} />
      )}
    </AuthGate>
  );
}
