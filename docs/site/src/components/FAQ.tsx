import { Card } from "@/components/ui/card";

interface FaqItem {
  question: string;
  answer: string;
}

const faqs: FaqItem[] = [
  {
    question: "What is Claude CodePro?",
    answer: "Claude CodePro is a professional development environment for Claude Code. It provides automated context management, spec-driven development, TDD enforcement, persistent memory, semantic search, quality hooks, and a modular rules system - all running inside a Dev Container.",
  },
  {
    question: "How does /ccp work?",
    answer: "The /ccp command is your single entry point. It handles everything: auto-setup on first run, creates a detailed plan for your approval, implements with TDD enforcement, verifies completion, and manages context across sessions automatically.",
  },
  {
    question: "Is Claude CodePro free?",
    answer: "Yes! Claude CodePro is completely free and open source under the AGPL-3.0 license. You can install it into any project and use all features without any cost.",
  },
  {
    question: "What IDEs are supported?",
    answer: "Claude CodePro works with VS Code, Cursor, Windsurf, and Antigravity. Any IDE with Dev Containers extension support should work. The experience is consistent across all supported IDEs.",
  },
  {
    question: "Do I need Docker?",
    answer: "Yes, you need a container runtime like Docker Desktop or OrbStack (macOS). Claude CodePro runs inside a Dev Container to provide complete isolation, consistent tooling, and cross-platform compatibility on Windows, Mac and Linux.",
  },
  {
    question: "How is context managed?",
    answer: "Auto-compact is disabled during installation (saves 20% context). The /ccp command handles session clears automatically when context fills up. Claude Mem preserves relevant information across sessions for seamless continuity.",
  },
];

const SectionHeader = ({ title, subtitle }: { title: string; subtitle?: string }) => (
  <div className="text-center mb-12">
    <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground mb-4">
      {title}
    </h2>
    {subtitle && (
      <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto">
        {subtitle}
      </p>
    )}
  </div>
);

const FAQ = () => {
  return (
    <section id="faq" className="py-20 lg:py-28 px-4 sm:px-6" aria-labelledby="faq-heading">
      <div className="max-w-4xl mx-auto">
        <SectionHeader title="Frequently Asked Questions" />

        <div className="grid sm:grid-cols-2 gap-4 sm:gap-6">
          {faqs.map((faq, index) => (
            <Card
              key={index}
              className="glass p-5 sm:p-6 hover:border-primary/50 transition-all duration-300"
            >
              <h3 className="text-foreground font-semibold text-sm sm:text-base mb-3">
                {faq.question}
              </h3>
              <p className="text-muted-foreground text-xs sm:text-sm">
                {faq.answer}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
