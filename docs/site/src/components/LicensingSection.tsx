import { ExternalLink, Check, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

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

const LicensingSection = () => {
  return (
    <section id="licensing" className="py-12 lg:py-16 px-4 sm:px-6" aria-labelledby="licensing-heading">
      <div className="max-w-5xl mx-auto">
        <SectionHeader
          title="Licensing"
          subtitle="Free for personal use, students, and nonprofits. Commercial license required for businesses."
        />

        <div className="grid md:grid-cols-2 gap-6 sm:gap-8">
          {/* Free License */}
          <Card className="glass p-6 sm:p-8 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-green-500 to-transparent" />
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-green-500/15 rounded-xl flex items-center justify-center">
                <Check className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground">Free</h3>
                <p className="text-sm text-muted-foreground">AGPL-3.0 License</p>
              </div>
            </div>

            <ul className="space-y-3 mb-6">
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Personal use</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Students and educators</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Nonprofit organizations</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Open source projects (AGPL-3.0)</span>
              </li>
            </ul>

            <p className="text-xs text-muted-foreground">
              Just install and use.
            </p>
          </Card>

          {/* Commercial License */}
          <Card className="glass p-6 sm:p-8 relative overflow-hidden border-primary/50">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-primary/15 rounded-xl flex items-center justify-center">
                <Building2 className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground">Commercial</h3>
                <p className="text-sm text-muted-foreground">Paid license required</p>
              </div>
            </div>

            <ul className="space-y-3 mb-6">
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Companies and organizations</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Freelancers and agencies</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">SaaS products and internal tools</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">Any revenue-generating use</span>
              </li>
            </ul>

            <Button asChild className="w-full">
              <a href="https://license.claude-code.pro" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Get License
              </a>
            </Button>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default LicensingSection;
