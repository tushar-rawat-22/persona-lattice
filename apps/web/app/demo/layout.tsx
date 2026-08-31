import type { ReactNode } from "react";

import { RetainedCaseNavigationSimulation } from "./retained-case-navigation-simulation";

export default function DemoLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <>
      {children}
      <div style={{ maxWidth: "1180px", margin: "0 auto", padding: "0 24px 40px" }}>
        <RetainedCaseNavigationSimulation />
      </div>
    </>
  );
}
