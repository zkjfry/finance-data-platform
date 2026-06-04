import type { ReactNode } from "react";

type TerminalCardProps = {
  children: ReactNode;
  href?: string | null;
};

export function TerminalCard({ children, href }: TerminalCardProps) {
  const content = <article className="terminal-card p-4">{children}</article>;

  if (!href) {
    return content;
  }

  return (
    <a href={href} target="_blank" rel="noreferrer">
      {content}
    </a>
  );
}