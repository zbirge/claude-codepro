import logoPng from "@/assets/logo.png";

interface LogoProps {
  variant?: "hero" | "footer";
}

const Logo = ({ variant = "hero" }: LogoProps) => {
  const sizeClass = variant === "hero"
    ? "w-full max-w-[280px] xs:max-w-[320px] sm:max-w-[400px] md:max-w-[500px] lg:max-w-[600px]"
    : "w-full max-w-[200px] sm:max-w-[240px]";

  return (
    <div className="inline-block p-6">
      <img
        src={logoPng}
        alt="Claude CodePro - Professional Development Environment for Claude Code"
        className={`${sizeClass} h-auto animate-glow`}
        loading={variant === "hero" ? "eager" : "lazy"}
      />
    </div>
  );
};

export default Logo;
