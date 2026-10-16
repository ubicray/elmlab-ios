//
//  ElmLab.swift
//  phyphox
//
//  Elm Lab: the home screen with illustrated cards and Azerbaijani as the language on first launch,
//  after the Android fork (github.com/Abbasovel/phyphox-android, branch elmlab,
//  ExperimentListActivity.setUpElmLabHome).
//

import UIKit

struct ElmLabCard {
    let image: String
    let title: String
    let subtitle: String
    ///File name of the bundled experiment the card opens
    let file: String
}

struct ElmLabSection {
    let heading: String
    let cards: [ElmLabCard]
}

enum ElmLab {
    static let background = UIColor(red: 14/255, green: 24/255, blue: 38/255, alpha: 1)
    static let cardBackground = UIColor(red: 20/255, green: 34/255, blue: 51/255, alpha: 1)
    static let cardBorder = UIColor(red: 43/255, green: 63/255, blue: 88/255, alpha: 1)
    static let mutedText = UIColor(red: 154/255, green: 170/255, blue: 189/255, alpha: 1)

    //Same cards and order as Android's full app: sensors, tools, then the museum demonstrations
    //(added to the experiments by tools/elmlab/strip_phyphox_org.py)
    static let sections: [ElmLabSection] = [
        ElmLabSection(heading: "elmlabSensorHeading", cards: [
            ElmLabCard(image: "elmlab_sensor_accelerometer", title: "elmlabSensorAccTitle", subtitle: "elmlabSensorAccSub", file: "accelerometer.phyphox"),
            ElmLabCard(image: "elmlab_sensor_linear", title: "elmlabSensorLinTitle", subtitle: "elmlabSensorLinSub", file: "linear_accelerometer.phyphox"),
            ElmLabCard(image: "elmlab_sensor_gyroscope", title: "elmlabSensorGyrTitle", subtitle: "elmlabSensorGyrSub", file: "gyroscope.phyphox"),
            ElmLabCard(image: "elmlab_sensor_magnetometer", title: "elmlabSensorMagTitle", subtitle: "elmlabSensorMagSub", file: "magnetometer.phyphox"),
            ElmLabCard(image: "elmlab_sensor_pressure", title: "elmlabSensorPreTitle", subtitle: "elmlabSensorPreSub", file: "pressure.phyphox"),
            ElmLabCard(image: "elmlab_sensor_light", title: "elmlabSensorLigTitle", subtitle: "elmlabSensorLigSub", file: "light.phyphox"),
            ElmLabCard(image: "elmlab_sensor_gps", title: "elmlabSensorGpsTitle", subtitle: "elmlabSensorGpsSub", file: "gps.phyphox")
        ]),
        ElmLabSection(heading: "elmlabToolsHeading", cards: [
            ElmLabCard(image: "elmlab_tool_tone", title: "elmlabToolToneTitle", subtitle: "elmlabToolToneSub", file: "tone_generator.phyphox"),
            ElmLabCard(image: "elmlab_tool_strobe", title: "elmlabToolStrobeTitle", subtitle: "elmlabToolStrobeSub", file: "strobe.phyphox"),
            ElmLabCard(image: "elmlab_tool_pendulum", title: "elmlabToolPendulumTitle", subtitle: "elmlabToolPendulumSub", file: "pendulum.phyphox"),
            ElmLabCard(image: "elmlab_tool_stopwatch", title: "elmlabToolStopwatchTitle", subtitle: "elmlabToolStopwatchSub", file: "acoustic_stopwatch.phyphox")
        ]),
        ElmLabSection(heading: "elmlabDemoHeading", cards: [
            ElmLabCard(image: "elmlab_demo_pressure", title: "elmlabDemoPressureTitle", subtitle: "elmlabDemoPressureSub", file: "elmlab_demo_1_pressure.phyphox"),
            ElmLabCard(image: "elmlab_demo_weightless", title: "elmlabDemoWeightlessTitle", subtitle: "elmlabDemoWeightlessSub", file: "elmlab_demo_2_weightless.phyphox"),
            ElmLabCard(image: "elmlab_demo_car", title: "elmlabDemoCarTitle", subtitle: "elmlabDemoCarSub", file: "elmlab_demo_3_car.phyphox"),
            ElmLabCard(image: "elmlab_demo_sound", title: "elmlabDemoSoundTitle", subtitle: "elmlabDemoSoundSub", file: "elmlab_demo_4_sound.phyphox")
        ])
    ]

    //MARK: - Language

    static let defaultLanguage = "az"
    private static let defaultLanguageSetKey = "elmlab_default_language_set"

    ///Whether this launch should make Azerbaijani the app's language: only once, only if nobody chose
    ///a language for the app yet (in the system settings, which store it as the app's
    ///AppleLanguages), and never under tests or automation, which pin their own language
    static func shouldSetDefaultLanguage(alreadySet: Bool, appLanguages: Any?, arguments: [String], environment: [String: String]) -> Bool {
        if alreadySet || appLanguages != nil { return false }
        if environment["XCTestConfigurationFilePath"] != nil { return false }
        if arguments.contains("-AppleLanguages") || arguments.contains("screenshot") { return false }
        if arguments.contains(where: { $0.hasPrefix("-phyphox") }) { return false }
        return true
    }

    ///Call before anything is localized: the bundle settles its language on first use
    static func applyDefaultLanguage() {
        let defaults = UserDefaults.standard
        let appDomain = Bundle.main.bundleIdentifier.flatMap { defaults.persistentDomain(forName: $0) }
        let process = ProcessInfo.processInfo
        guard shouldSetDefaultLanguage(alreadySet: defaults.bool(forKey: defaultLanguageSetKey),
                                       appLanguages: appDomain?["AppleLanguages"],
                                       arguments: process.arguments,
                                       environment: process.environment) else { return }
        defaults.set(true, forKey: defaultLanguageSetKey)
        defaults.set([defaultLanguage], forKey: "AppleLanguages")
    }
}

//MARK: - Home screen

///One illustrated card: picture, title and a line below it
final class ElmLabCardView: UIControl {
    let card: ElmLabCard
    let imageView = UIImageView()
    let titleLabel = UILabel()
    let subtitleLabel = UILabel()

    private let padding: CGFloat = 8

    init(card: ElmLabCard) {
        self.card = card
        super.init(frame: .zero)
        backgroundColor = ElmLab.cardBackground
        layer.cornerRadius = 20
        layer.borderWidth = 1
        layer.borderColor = ElmLab.cardBorder.cgColor
        clipsToBounds = true

        imageView.image = UIImage(named: card.image)
        imageView.contentMode = .scaleAspectFit
        imageView.layer.cornerRadius = 12
        imageView.clipsToBounds = true

        titleLabel.text = localize(card.title)
        titleLabel.font = UIFontMetrics(forTextStyle: .headline).scaledFont(for: .boldSystemFont(ofSize: 18))
        titleLabel.adjustsFontForContentSizeCategory = true
        titleLabel.textColor = .white
        titleLabel.numberOfLines = 0

        subtitleLabel.text = localize(card.subtitle)
        subtitleLabel.font = UIFontMetrics(forTextStyle: .footnote).scaledFont(for: .systemFont(ofSize: 13))
        subtitleLabel.adjustsFontForContentSizeCategory = true
        subtitleLabel.textColor = ElmLab.mutedText
        subtitleLabel.numberOfLines = 0

        for v in [imageView, titleLabel, subtitleLabel] {
            v.isUserInteractionEnabled = false
            addSubview(v)
        }

        isAccessibilityElement = true
        accessibilityTraits = .button
        accessibilityLabel = (titleLabel.text ?? "") + ", " + (subtitleLabel.text ?? "")
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var isHighlighted: Bool {
        didSet { alpha = isHighlighted ? 0.7 : 1 }
    }

    override func sizeThatFits(_ size: CGSize) -> CGSize {
        let inner = size.width - 2 * padding
        let text = CGSize(width: inner - 8, height: .greatestFiniteMagnitude)
        let height = padding + inner + 8 + titleLabel.sizeThatFits(text).height
            + subtitleLabel.sizeThatFits(text).height + 4 + padding
        return CGSize(width: size.width, height: ceil(height))
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let inner = bounds.width - 2 * padding
        imageView.frame = CGRect(x: padding, y: padding, width: inner, height: inner)
        let text = CGSize(width: inner - 8, height: .greatestFiniteMagnitude)
        let title = titleLabel.sizeThatFits(text)
        titleLabel.frame = CGRect(x: padding + 4, y: imageView.frame.maxY + 8, width: inner - 8, height: title.height)
        let subtitle = subtitleLabel.sizeThatFits(text)
        subtitleLabel.frame = CGRect(x: padding + 4, y: titleLabel.frame.maxY, width: inner - 8, height: subtitle.height)
    }
}

///The Elm Lab home screen: the Elm Lab header with the info button, then each section as a heading
///over a grid of cards (two columns on phones, four on wider screens)
final class ElmLabHomeView: UIScrollView {
    var onSelect: ((ElmLabCard) -> Void)?
    var onInfo: (() -> Void)?

    let infoButton = UIButton(type: .infoLight)
    private let header = UIImageView(image: UIImage(named: "phyphox_dark"))
    private var headings: [UILabel] = []
    private var cardViews: [[ElmLabCardView]] = []

    private let padding: CGFloat = 10
    private let cardMargin: CGFloat = 6
    ///What the current layout was made for: a scroll view lays out on every scrolled frame
    private var layoutKey: String?
    private var generation = 0

    var sections: [ElmLabSection] = [] {
        didSet { rebuild() }
    }

    init(sections: [ElmLabSection]) {
        super.init(frame: .zero)
        backgroundColor = ElmLab.background
        contentInsetAdjustmentBehavior = .never
        alwaysBounceVertical = true
        indicatorStyle = .white

        header.contentMode = .scaleAspectFit
        header.isAccessibilityElement = true
        header.accessibilityLabel = localize("app_name")
        header.accessibilityTraits = .header
        addSubview(header)

        infoButton.tintColor = .white
        infoButton.accessibilityLabel = localize("info")
        infoButton.addTarget(self, action: #selector(infoPressed), for: .touchUpInside)
        addSubview(infoButton)

        self.sections = sections
        rebuild()
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func rebuild() {
        headings.forEach { $0.removeFromSuperview() }
        cardViews.joined().forEach { $0.removeFromSuperview() }
        headings = []
        cardViews = []
        for section in sections where !section.cards.isEmpty {
            let heading = UILabel()
            heading.text = localize(section.heading)
            heading.font = UIFontMetrics(forTextStyle: .title1).scaledFont(for: .boldSystemFont(ofSize: 26))
            heading.adjustsFontForContentSizeCategory = true
            heading.textColor = .white
            heading.numberOfLines = 0
            heading.accessibilityTraits = .header
            addSubview(heading)
            headings.append(heading)

            var views: [ElmLabCardView] = []
            for card in section.cards {
                let view = ElmLabCardView(card: card)
                view.addTarget(self, action: #selector(cardPressed(_:)), for: .touchUpInside)
                addSubview(view)
                views.append(view)
            }
            cardViews.append(views)
        }
        generation += 1
        setNeedsLayout()
    }

    @objc private func infoPressed() {
        onInfo?()
    }

    @objc private func cardPressed(_ sender: ElmLabCardView) {
        onSelect?(sender.card)
    }

    override func safeAreaInsetsDidChange() {
        super.safeAreaInsetsDidChange()
        setNeedsLayout()
    }

    override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        setNeedsLayout()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let key = "\(bounds.width) \(safeAreaInsets) \(traitCollection.preferredContentSizeCategory.rawValue) \(generation)"
        guard key != layoutKey else { return }
        layoutKey = key
        let left = safeAreaInsets.left + padding
        let width = bounds.width - safeAreaInsets.left - safeAreaInsets.right - 2 * padding
        var y = safeAreaInsets.top + padding

        //Header row: the Elm Lab logo on the left, the info button on the right
        let headerHeight: CGFloat = 56
        let logoSize = header.image?.size ?? CGSize(width: 1, height: 1)
        header.frame = CGRect(x: left + 6, y: y + 6, width: headerHeight * logoSize.width / logoSize.height, height: headerHeight)
        infoButton.frame = CGRect(x: left + width - 48, y: y + 6 + (headerHeight - 48) / 2, width: 48, height: 48)
        y += headerHeight + 12

        let columns = width >= 700 ? 4 : 2
        let cardWidth = floor((width - CGFloat(columns) * 2 * cardMargin) / CGFloat(columns))
        for (heading, views) in zip(headings, cardViews) {
            y += 18
            let size = heading.sizeThatFits(CGSize(width: width - 8, height: .greatestFiniteMagnitude))
            heading.frame = CGRect(x: left + 8, y: y, width: width - 8, height: size.height)
            y += size.height + 4

            for row in stride(from: 0, to: views.count, by: columns) {
                let rowViews = views[row..<min(row + columns, views.count)]
                let height = rowViews.map { $0.sizeThatFits(CGSize(width: cardWidth, height: .greatestFiniteMagnitude)).height }.max() ?? 0
                for (i, view) in rowViews.enumerated() {
                    view.frame = CGRect(x: left + cardMargin + CGFloat(i) * (cardWidth + 2 * cardMargin), y: y + cardMargin, width: cardWidth, height: height)
                }
                y += height + 2 * cardMargin
            }
        }
        contentSize = CGSize(width: bounds.width, height: y + padding + safeAreaInsets.bottom)
    }
}
